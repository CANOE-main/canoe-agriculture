# -*- coding: utf-8 -*-
"""
Created on Fri Aug 15 14:12:38 2025

Updated on Oct 7 2025 — Adds logic to assign any remainder (<1) to diesel (dsl)
@author: david
"""

from __future__ import annotations
import pandas as pd
from typing import Dict
import numpy as np
from canoe_agriculture.common import setup_logging
from canoe_schema.v3_2.models import LimitTechInputSplitAnnual

logger = setup_logging()

COM_TO_COL = {"elc": 15, "ng": 16, "dsl": 18, "gsl": 17}


def build_limit_tech_input_split_agri(
    comb_dict: Dict[str, pd.DataFrame], loaded_df: dict[str, pd.DataFrame]
) -> Dict[str, pd.DataFrame]:
    dom = comb_dict["__domain__"]
    ids = comb_dict["__ids__"]
    province_list = dom["province_list"]
    sector_abv = dom["sector_abv"]
    periods = dom["periods"]
    atl_pro = set(dom["atl_pro"])

    rows = []
    for region in province_list:
        for per in periods:
            tis_vals: list[float | str] = []
            coms: list[str] = []

            # Load values from dataframes
            for com, idx in COM_TO_COL.items():
                try:
                    value = (
                        loaded_df["ATL"]["2022"][idx]
                        if region in atl_pro
                        else loaded_df[region]["2022"][idx]
                    )
                except Exception:
                    value = None
                if value in (None, "0.0"):
                    continue
                elif value in ("n.a.", "X"):
                    tis = "na"
                else:
                    tis = round(float(value) / 100, 3)
                tis_vals.append(tis)
                coms.append(com)

            na_count = tis_vals.count("na")
            float_vals = [v for v in tis_vals if isinstance(v, float)]
            total_known = sum(float_vals)

            # If total exceeds 1.0, correct smallest float downward
            if total_known > 1.0 and float_vals:
                excess = round(total_known - 1.0, 3)
                min_val = min(float_vals)
                min_idx = tis_vals.index(min_val)
                corrected = max(0.0, round(min_val - excess, 3))
                tis_vals[min_idx] = corrected
                float_vals = [v for v in tis_vals if isinstance(v, float)]
                total_known = sum(float_vals)

            # If total is less than 1, remainder goes to 'dsl'
            if total_known < 1.0:
                remainder = round(0.999 - total_known, 3)
                if "dsl" in coms:
                    dsl_idx = coms.index("dsl")
                    if isinstance(tis_vals[dsl_idx], float):
                        tis_vals[dsl_idx] = round(tis_vals[dsl_idx] + remainder, 3)
                    elif tis_vals[dsl_idx] == "na":
                        tis_vals[dsl_idx] = remainder
                    else:
                        tis_vals.append(remainder)
                        coms.append("dsl")
                else:
                    # If no dsl entry exists, create one
                    tis_vals.append(remainder)
                    coms.append("dsl")

            # Recompute total for safety
            float_vals = [v for v in tis_vals if isinstance(v, float)]
            total_known = sum(float_vals)

            # Build dataframe rows
            for i, tis in enumerate(tis_vals):
                com = coms[i]
                if tis != "na":
                    final_val = float(tis)
                else:
                    if na_count == 0:
                        continue
                    missing_total = max(0.0, 1.0 - total_known)
                    final_val = round(missing_total / na_count, 3)

                rows.append(
                    LimitTechInputSplitAnnual(
                        region=region,
                        period=per,
                        input_comm=f"A_{com}",
                        tech=f"{sector_abv}AGRI",
                        operator="ge",
                        proportion=final_val,
                        notes="Calculated from NRCan comprehensive database. If values were n.a., remainder to 100% assigned to diesel.",
                        data_source="A1",
                        dq_cred=2,
                        dq_geog=1,
                        dq_struc=2,
                        dq_tech=3,
                        dq_time=3,
                        data_id=ids[region],
                    )
                )

    df = pd.DataFrame([row.model_dump(mode="python") for row in rows])
    comb_dict["LimitTechInputSplitAnnual"] = pd.concat(
        [comb_dict["LimitTechInputSplitAnnual"], df], ignore_index=True
    )
    logger.info("LimitTechInputSplitAnnual rows: %d", len(rows))
    return comb_dict
