from sqlite3 import Connection
from loguru import logger
from canoe_schema.v4_0.models import TimePeriod
from canoe_agriculture.common import CANOEAgricultureConfig


def check_missing_periods(
    db_conn: Connection, periods_e: list[int], periods_f: list[int]
):
    cur = db_conn.cursor()
    results = []

    for values, flag in [(periods_e, "e"), (periods_f, "f")]:
        placeholders = ", ".join("?" * len(values))
        query = f"""
            SELECT period, '{flag}' AS expected_flag
            FROM {TimePeriod.__table_name__}
            WHERE period IN ({placeholders})
              AND flag != ?
        """
        cur.execute(query, (*values, flag))
        wrong_flag = {row[0] for row in cur.fetchall()}

        cur.execute(
            f"SELECT period FROM {TimePeriod.__table_name__} WHERE period IN ({placeholders})",
            values,
        )
        found = {row[0] for row in cur.fetchall()}

        missing = set(values) - found
        results += [(val, flag) for val in missing | wrong_flag]

    return results


def validate_db_against_config(
    module_config: CANOEAgricultureConfig, db_conn: Connection
):
    # Verify if all existing and future periods already exist in the database
    missing_periods = check_missing_periods(
        db_conn, module_config.existing_periods, module_config.future_periods
    )

    if len(missing_periods) > 0:
        vals, flags = zip(*missing_periods)
        if module_config.validation_behavior == "error":
            raise ValueError(f"Value {vals} missing or wrong flag (expected '{flags}')")
        logger.warning(f"Value {vals} missing or wrong flag (expected '{flags}')")

    return True
