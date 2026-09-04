# -*- coding: utf-8 -*-
from __future__ import annotations
from sqlite3 import Cursor
import pandas as pd
from loguru import logger
from typing import Dict
from canoe_agriculture.common import CANOEAgricultureConfig
from canoe_schema.v4_0.models import Efficiency, LimitTechInputSplitAnnual


def _to_output_comm(tech: str) -> str | None:
    parts = tech.split("_", 1)
    if len(parts) == 2:
        prefix, name = parts
        return f"{prefix}_d_{name.lower()}"
    return None


def build_limit_tech_input_and_efficiency(
    module_config: CANOEAgricultureConfig,
    db_cursor: Cursor,
    comb_dict: Dict[str, pd.DataFrame],
    nrcan_df: dict[str, pd.DataFrame],
) -> Dict[str, pd.DataFrame]:
    dom = comb_dict["__domain__"]
    ids = comb_dict["__ids__"]
    atl_pro = set(dom["atl_pro"])
    remainder_fuel = module_config.remainder_fuel_limit_tech_annual

    configured_fuels = {f.shortname for f in module_config.input_fuels}
    if remainder_fuel not in configured_fuels:
        raise ValueError(
            f"Remainder fuel '{remainder_fuel}' is not defined in input_fuels. "
            f"Available fuels: {sorted(configured_fuels)}"
        )

    efficiency_rows = []
    limit_tech_annual_rows = []
    for region in module_config.province_list:
        for per in module_config.future_periods:
            tis_vals: list[float | str] = []
            coms: list[str] = []

            nrcan_key = "ATL" if region in atl_pro else region
            nrcan_year = str(module_config.NRCan_year)

            for fuel in module_config.input_fuels:
                try:
                    value = nrcan_df[nrcan_key][nrcan_year][fuel.nrcan_row_idx]
                except Exception:
                    value = None
                if value in (None, "0.0"):
                    continue
                elif value in ("n.a.", "X"):
                    tis = "na"
                else:
                    tis = round(float(value) / 100, 3)
                tis_vals.append(tis)
                coms.append(fuel.shortname)

            na_count = tis_vals.count("na")
            float_vals = [v for v in tis_vals if isinstance(v, float)]
            total_known = sum(float_vals)

            # If total exceeds 1.0, correct the smallest value downward
            if total_known > 1.0 and float_vals:
                excess = round(total_known - 1.0, 3)
                min_val = min(float_vals)
                tis_vals[tis_vals.index(min_val)] = max(0.0, round(min_val - excess, 3))
                float_vals = [v for v in tis_vals if isinstance(v, float)]
                total_known = sum(float_vals)

            # Remainder below 1.0 is assigned to remainder_fuel
            if total_known < 1.0:
                remainder = round(0.999 - total_known, 3)
                if remainder_fuel in coms:
                    dsl_idx = coms.index(remainder_fuel)
                    if isinstance(tis_vals[dsl_idx], float):
                        tis_vals[dsl_idx] = round(tis_vals[dsl_idx] + remainder, 3)
                    else:  # "na"
                        tis_vals[dsl_idx] = remainder
                else:
                    tis_vals.append(remainder)
                    coms.append(remainder_fuel)

            float_vals = [v for v in tis_vals if isinstance(v, float)]
            total_known = sum(float_vals)

            for com, tis in zip(coms, tis_vals):
                if tis != "na":
                    final_val = float(tis)
                else:
                    if na_count == 0:
                        continue
                    final_val = round(max(0.0, 1.0 - total_known) / na_count, 3)

                limit_tech_annual_rows.append(
                    LimitTechInputSplitAnnual(
                        region=region,
                        period=per,
                        input_comm=f"{module_config.sector_initial}_{com}",
                        tech=f"{module_config.sector_initial}_{module_config.sector_abv}",
                        operator="ge",
                        proportion=final_val,
                        notes=f"Calculated from NRCan comprehensive database. If values were n.a., remainder to 100% assigned to {remainder_fuel}.",
                        data_source="A1",
                        dq_cred=2,
                        dq_geog=1,
                        dq_struc=2,
                        dq_tech=3,
                        dq_time=3,
                        data_id=ids[region],
                    )
                )

                efficiency_rows.append(
                    Efficiency(
                        region=region,
                        input_comm=f"{module_config.sector_initial}_{com}",
                        tech=f"{module_config.sector_initial}_{module_config.sector_abv}",
                        vintage=per,
                        output_comm=_to_output_comm(
                            f"{module_config.sector_initial}_{module_config.sector_abv}"
                        ),
                        efficiency=1.0,
                        notes="All technologies assumed efficiency=1; commodities from NRCan Comp DB",
                        data_source="A1",
                        data_id=ids[region],
                    )
                )

    db_cursor.executemany(
        *LimitTechInputSplitAnnual.bulk_insert_or_ignore_sql(limit_tech_annual_rows)
    )
    logger.info(f"LimitTechInputSplitAnnual rows: {len(limit_tech_annual_rows)}")
    db_cursor.executemany(*Efficiency.bulk_insert_or_ignore_sql(efficiency_rows))
    logger.info(f"Efficiency rows: {len(efficiency_rows)}")
