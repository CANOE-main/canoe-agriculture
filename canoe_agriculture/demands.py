# -*- coding: utf-8 -*-
"""
Created on Fri Aug 15 14:21:58 2025

@author: david
"""

from __future__ import annotations
from itertools import product
from sqlite3 import Cursor
import pandas as pd
from typing import Dict
from canoe_agriculture.common import CANOEAgricultureConfig, setup_logging
from canoe_schema.v4_0.models import Demand, ExistingCapacity

logger = setup_logging()

# TODO This values could be put somewhere either more directly tied to their purpose
# or where we generally put parameters
ATL_MAP = {
    "PEI": "Prince Edward Island",
    "NS": "Nova Scotia",
    "NB": "New Brunswick",
    "NLLAB": "Newfoundland and Labrador",
}
SECTOR_KEY = "Agriculture, fishing, hunting and trapping"


def _gdp_scalers(pop_df: pd.DataFrame, periods: list[int]) -> dict[int, float]:
    """
    Computes a series of GDP factors relative to the first period in the data
    """
    df = pop_df.copy()
    df = df[df["Year"].isin(periods)]
    df = df[df["Variable"] == "Real Gross Domestic Product ($2012 Millions)"]
    df = df[df["Scenario"] == "Global Net-zero"]
    df = df.sort_values("Year").set_index("Year")["Value"]
    df = df / df.iloc[0]
    return df.to_dict()


def _get_atl_share(province: str, shares: dict[str, dict[str, float]]) -> float | None:
    """
    Get the share of the atlantic provinces corresponding to this province
    """
    try:
        return float(shares[SECTOR_KEY][ATL_MAP[province]])
    except Exception:
        return None


def build_demand_and_capacity_agri(
    module_config: CANOEAgricultureConfig,
    comb_dict: Dict[str, pd.DataFrame],
    loaded_df: dict[str, pd.DataFrame],
    pop_df: pd.DataFrame,
    atl_shares: dict[str, dict[str, float]],
    db_cursor: Cursor,
) -> Dict[str, pd.DataFrame]:
    dom = comb_dict["__domain__"]
    ids = comb_dict["__ids__"]
    atl_pro = set(dom["atl_pro"])

    gdp_scale = _gdp_scalers(pop_df, module_config.future_periods)

    # Compute the adjusted demand values
    demand_tuples = []
    existing_cap_tuples = []
    for province, year in product(
        module_config.province_list,
        module_config.existing_periods + module_config.future_periods,
    ):
        nrcan_key = "ATL" if province in atl_pro else province
        gdp_factor = gdp_scale[year] if year > min(module_config.future_periods) else 1
        atl_factor = _get_atl_share(province, atl_shares)
        atl_factor = 1 if (atl_factor is None or atl_factor == 1) else atl_factor

        # Base values from NRCan table (first row index 0 as in original)
        # base means NRCan table year
        base_year = (
            module_config.NRCan_year if year in module_config.future_periods else year
        )
        assert (
            str(base_year) in loaded_df[nrcan_key].columns
        ), f"Year {base_year} not found in NRCan Demand values, required for computing demand/capacity of {year}"
        base_demand_value = float(loaded_df[nrcan_key][str(base_year)][0])
        adjusted_value = base_demand_value * gdp_factor * atl_factor

        # Data provenance columns
        if year in module_config.existing_periods:
            notes, ref = "Existing capacity from NRCan baseline", "A1"
        elif year == min(module_config.future_periods):
            notes, ref = "Value from NRCan Comprehensive DB", "A1"
        else:
            notes, ref = "Scaled by GDP growth from CER CEF", "A2"

        if nrcan_key == "ATL" and atl_factor != 1:
            if year in module_config.future_periods:
                ref = "A4"
            else:
                ref = "A3"

        # Add to ready tuples
        if year in module_config.future_periods:
            demand_tuples.append((province, year, adjusted_value, notes, ref))
        else:
            existing_cap_tuples.append((province, year, adjusted_value, notes, ref))

    dem_rows = [
        Demand(
            region=province,
            period=int(year),
            commodity=f"{module_config.sector_initial}_d_agri",
            demand=adjusted_value,
            units="PJ",
            notes=notes,
            data_source=ref,
            dq_cred=1,
            dq_geog=1,
            dq_struc=2,
            dq_tech=3,
            dq_time=2,
            data_id=ids[province],
        )
        for province, year, adjusted_value, notes, ref in demand_tuples
    ]
    # NOTE INSERT OR IGNORE prefered for idempotency
    db_cursor.executemany(*Demand.bulk_insert_or_ignore_sql(dem_rows))
    logger.info("Demand rows: %d", len(dem_rows))

    # Input Existing Capacities
    # TODO Check if this is consistent with older code and if it's correct
    cap_rows = [
        ExistingCapacity(
            region=province,
            vintage=int(year),
            tech=f"{module_config.sector_initial}_{module_config.sector_abv}",
            capacity=adjusted_value,
            units="PJ",
            notes=notes,
            data_source=ref,
            dq_cred=1,
            dq_geog=1,
            dq_struc=2,
            dq_tech=3,
            dq_time=2,
            data_id=ids[province],
        )
        for province, year, adjusted_value, notes, ref in existing_cap_tuples
    ]
    # NOTE INSERT OR IGNORE prefered for idempotency
    if len(cap_rows) > 0:
        db_cursor.executemany(*ExistingCapacity.bulk_insert_or_ignore_sql(cap_rows))
    logger.info("ExistingCapacity rows: %d", len(cap_rows))

    # # ExistingCapacity from 2021 baseline
    # base2021 = {p: float(loaded_df['ATL']['2021'][0]) if p in atl_pro else float(loaded_df[p]['2021'][0]) for p in province_list}
    # cap_rows = []
    # for pro in province_list:
    #     for sec in sector_list:
    #         val = base2021[pro]
    #         ref = 'A1'
    #         if pro in atl_pro:
    #             split = _atl_split(val, pro, atl_shares)
    #             if split is None: continue
    #             val, ref = split, '[3]'
    #         cap_rows.append([pro, sector_abv+sec, 2021, float(val), 'PJ', 'Existing capacity from NRCan baseline', ref, 1,1,2,3,2, ids[pro]])

    # cap_df = pd.DataFrame(cap_rows, columns=comb_dict['ExistingCapacity'].columns)
    # comb_dict['ExistingCapacity'] = pd.concat([comb_dict['ExistingCapacity'], cap_df], ignore_index=True)
    # logger.info("ExistingCapacity rows: %d", len(cap_rows))

    return comb_dict
