# -*- coding: utf-8 -*-
"""
Created on Sun Aug 17 13:36:00 2025

@author: david
"""

from __future__ import annotations
import argparse
import sqlite3
from canoe_agriculture.common import (
    setup_logging,
    project_paths,
    CANOEAgricultureConfig,
)
from canoe_agriculture.setup import load_runtime_agri
from canoe_agriculture.validation import validate_db_against_config
from canoe_agriculture.techcom import add_technology_and_fuel_commodities
from canoe_agriculture.data_scraper import load_cached_or_fetch_agri
from canoe_agriculture.statcan import load_statcan_agri_shares
from canoe_agriculture.demands import build_demand_and_capacity_agri
from canoe_agriculture.techinput import build_limit_tech_input_split_agri
from canoe_agriculture.efficiency import build_efficiency_agri
from canoe_agriculture.post_processing import add_datasets_and_sources_agri

logger = setup_logging()


# def write_comb_dict_to_db(db_path, tables, comb_dict: Dict[str, pd.DataFrame]) -> None:
#     with sqlite3.connect(db_path) as conn:
#         for table in tables:
#             df = comb_dict.get(table)
#             if df is None or df.empty:
#                 logger.warning("Skipping empty table: %s", table)
#                 continue
#             df.to_sql(table, conn, if_exists="append", index=False)
#             logger.info("Wrote %d rows to %s", len(df), table)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Agriculture ETL Aggregator (with ATL split)"
    )
    parser.add_argument(
        "--cfg", default="input/config.toml", help="Path to configuration file"
    )
    args = parser.parse_args()
    cfg = CANOEAgricultureConfig.validate_from_toml(args.cfg)

    ##### Required external data sources
    # NRCan and CER data retrieval/cache
    nrcan_df, pop_df = load_cached_or_fetch_agri(
        cfg.NRCan_year, project_paths()["cache"]
    )

    # StatCan ATL shares (agriculture)
    atl_shares = load_statcan_agri_shares(project_paths()["cache"])

    ##### Module logic
    # Init runtime
    db_path, cfg, tables, comb_dict = load_runtime_agri(cfg=cfg)
    db_conn = sqlite3.connect(db_path)
    db_cursor = db_conn.cursor()

    # 0) Validate database against configuration
    validate_db_against_config(cfg, db_conn)

    # 1) Technology/Commodity scaffolding
    add_technology_and_fuel_commodities(
        module_config=cfg, db_cursor=db_cursor, data_id_code=comb_dict["__ids__"]["CAN"]
    )

    # 2) Demand + ExistingCapacity (GDP scaling + ATL split)
    comb_dict = build_demand_and_capacity_agri(
        cfg, comb_dict, nrcan_df, pop_df, atl_shares, db_cursor
    )

    # 3) LimitTechInputSplitAnnual from NRCan shares (ATL uses ATL table)
    comb_dict = build_limit_tech_input_split_agri(cfg, db_cursor, comb_dict, nrcan_df)

    # 6) Efficiency (derived from techinput)
    comb_dict = build_efficiency_agri(comb_dict)

    # 7) Costs
    # comb_dict = build_cost_invest_agri(comb_dict)

    # 8) Post-processing
    comb_dict = add_datasets_and_sources_agri(comb_dict)
    # 9) Testing purposes, add region and times in
    # comb_dict = add_time_agri(comb_dict)

    # 10) Persist
    # write_comb_dict_to_db(db_path, tables, comb_dict)

    db_conn.commit()
    db_conn.close()
    logger.info("Done. SQLite written to %s", db_path)


if __name__ == "__main__":
    main()
