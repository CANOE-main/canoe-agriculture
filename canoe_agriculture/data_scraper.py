# -*- coding: utf-8 -*-
"""
Created on Wed Aug 13 10:50:43 2025

@author: david
"""

from __future__ import annotations
from io import StringIO
from pathlib import Path
import pickle
from typing import Dict
import requests
import pandas as pd
from loguru import logger
from canoe_agriculture.common import ensure_dir


NRCan_URL = "https://oee.nrcan.gc.ca/corporate/statistics/neud/dpa/showTable.cfm"
CER_URL = (
    "https://www.cer-rec.gc.ca/open/energy/energyfutures2023/macro-indicators-2023.csv"
)

PROV_CODES = ["on", "ab", "qc", "bct", "mb", "sk", "atl"]


def _session(timeout: int = 45) -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": "agri-etl/1.0"})
    s.timeout = timeout
    return s


def load_cached_or_fetch_agri(
    nrcan_year: int, cache_dir: Path
) -> tuple[Dict[str, pd.DataFrame], pd.DataFrame]:
    ensure_dir(cache_dir)
    df_cache = cache_dir / "dataframes.pkl"
    pop_cache = cache_dir / "pop_df.pkl"

    if df_cache.exists():
        logger.info(f"Cache hit: {df_cache}")
        loaded_df = pickle.loads(df_cache.read_bytes())
    else:
        sess = _session()
        dict_comb: Dict[str, pd.DataFrame] = {}
        for code in PROV_CODES:
            params = {
                "type": "CP",
                "sector": "agr",
                "juris": code,
                "year": nrcan_year,
                "rn": "1",
                "page": "0",
            }
            r = sess.get(NRCan_URL, params=params, timeout=45)
            r.raise_for_status()
            tables = pd.read_html(StringIO(r.text))
            if not tables:
                raise ValueError(f"No tables for {code}")
            df = tables[0]
            mapping = {
                "ab": "AB",
                "on": "ON",
                "bct": "BC",
                "mb": "MB",
                "sk": "SK",
                "qc": "QC",
                "atl": "ATL",
            }
            dict_comb[mapping[code]] = df
        loaded_df = dict_comb
        df_cache.write_bytes(pickle.dumps(loaded_df))

    if pop_cache.exists():
        logger.info(f"Cache hit: {pop_cache}")
        pop_df = pickle.loads(pop_cache.read_bytes())
    else:
        r = _session().get(CER_URL, timeout=45)
        r.raise_for_status()
        pop_df = pd.read_csv(StringIO(r.text))
        pop_cache.write_bytes(pickle.dumps(pop_df))

    return loaded_df, pop_df
