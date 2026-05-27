# -*- coding: utf-8 -*-
"""
Created on Thu Aug 14 19:26:36 2025

@author: david
"""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Dict
import pandas as pd

from canoe_agriculture.common import setup_logging, Config, ensure_dir, project_paths

logger = setup_logging()


def schema_file_for(cfg: Config) -> Path:
    paths = project_paths()
    if cfg.schema_version != 31:
        return paths["schema"] / f"schema_{cfg.schema_version}.sql"
    return paths["schema"] / "schema_3_1.sql"


def prepare_database(db_path: Path, schema_sql: str) -> list[str]:
    ensure_dir(db_path.parent)
    if db_path.exists():
        db_path.unlink()
        logger.info("Removed existing DB: %s", db_path)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_sql)
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    logger.info("Prepared new DB with %d tables", len(tables))
    return tables


def create_empty_comb_dict(db_path: Path, tables: list[str]) -> Dict[str, pd.DataFrame]:
    comb_dict: Dict[str, pd.DataFrame] = {}
    with sqlite3.connect(db_path) as conn:
        for table in tables:
            cols = conn.execute(f"PRAGMA table_info('{table}');").fetchall()
            names = [c[1] for c in cols]
            comb_dict[table] = pd.DataFrame(columns=names)
    return comb_dict


def load_runtime_agri(cfg: Config) -> tuple[Path, Config, list[str], Dict[str, pd.DataFrame]]:
    paths = project_paths()

    # domain constants (from your original script)
    sector_abv = "A_"
    sector_list = ["AGRI"]
    sector_list_ex = ["Agriculture"]
    province_list = ["AB", "ON", "BC", "MB", "SK", "QC", "PEI", "NS", "NB", "NLLAB"]
    atl_pro = ["PEI", "NS", "NB", "NLLAB"]
    commodity_list = ["elc", "ng", "dsl", "gsl"]
    commodity_list_ex = ["Electricity", "Natural Gas", "Diesel", "Gasoline"]

    # ids
    id_dict = {p: f"AGRIHR{p}{cfg.version}" for p in province_list}
    id_dict["CAN"] = f"AGRIHR{cfg.version}"

    db_path = paths["outputs"] / cfg.db_name
    schema_sql = schema_file_for(cfg).read_text(encoding="utf-8")
    tables = prepare_database(db_path, schema_sql)
    comb_dict = create_empty_comb_dict(db_path, tables)

    comb_dict["__domain__"] = {
        "sector": "Agriculture",
        "sector_abv": sector_abv,
        "sector_list": sector_list,
        "sector_list_ex": sector_list_ex,
        "province_list": province_list,
        "atl_pro": atl_pro,
        "commodity_list": commodity_list,
        "commodity_list_ex": commodity_list_ex,
        "periods": cfg.periods,
    }
    comb_dict["__ids__"] = id_dict
    comb_dict["__version__"] = cfg.version

    return db_path, cfg, tables, comb_dict