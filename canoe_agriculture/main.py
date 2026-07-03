# -*- coding: utf-8 -*-
"""
Created on Sun Aug 17 13:36:00 2025

@author: david
"""

from __future__ import annotations
import argparse
import sqlite3
from loguru import logger
from canoe_agriculture.common import (
    project_paths,
    CANOEAgricultureConfig,
)
from canoe_agriculture.setup import load_runtime_agri
from canoe_agriculture.validation import validate_db_against_config
from canoe_agriculture.techcom import add_technology_and_fuel_commodities
from canoe_agriculture.data_scraper import load_cached_or_fetch_agri
from canoe_agriculture.statcan import load_statcan_agri_shares
from canoe_agriculture.demands import build_demand_and_capacity_agri
from canoe_agriculture.techinput import build_limit_tech_input_and_efficiency
from canoe_agriculture.post_processing import add_datasets_and_sources_agri


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
    build_demand_and_capacity_agri(
        cfg, comb_dict, nrcan_df, pop_df, atl_shares, db_cursor
    )

    # 3) LimitTechInputSplitAnnual from NRCan shares (ATL uses ATL table)
    # Efficiency rows are built here but default to 1
    build_limit_tech_input_and_efficiency(
        cfg, db_cursor, comb_dict, nrcan_df
    )

    # Costs
    # comb_dict = build_cost_invest_agri(comb_dict)

    # 4) Data provenance: register the datasets used
    add_datasets_and_sources_agri(db_cursor, comb_dict)

    db_conn.commit()
    db_conn.close()
    logger.info(f"Done. SQLite written to {db_path}")


if __name__ == "__main__":
    main()
