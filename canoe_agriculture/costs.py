# -*- coding: utf-8 -*-
"""
Created on Fri Aug 15 12:33:38 2025

@author: david
"""

from __future__ import annotations
import pandas as pd
from typing import Dict
from canoe_agriculture.common import setup_logging
import numpy as np

logger = setup_logging()


def build_cost_invest_agri(
    comb_dict: Dict[str, pd.DataFrame],
) -> Dict[str, pd.DataFrame]:
    """
    TODO This needs refactoring before it can be used
    """
    dom = comb_dict["__domain__"]
    ids = comb_dict["__ids__"]
    province_list = dom["province_list"]
    periods = dom["periods"]
    rows = []
    vintage = min(periods)
    for province in province_list:
        rows.append(
            [
                province,
                "A_AGRI",
                vintage,
                0.1,
                "M$/PJ",
                "Arbitrary amount for first time period",
                np.nan,
                np.nan,
                np.nan,
                np.nan,
                np.nan,
                np.nan,
                ids[province],
            ]
        )
    df = pd.DataFrame(rows, columns=comb_dict["CostInvest"].columns)
    comb_dict["CostInvest"] = pd.concat(
        [comb_dict["CostInvest"], df], ignore_index=True
    )
    logger.info(f"CostInvest rows: {len(rows)}")
    return comb_dict
