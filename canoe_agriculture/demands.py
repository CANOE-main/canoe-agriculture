# -*- coding: utf-8 -*-
"""
Created on Fri Aug 15 14:21:58 2025

@author: david
"""
from __future__ import annotations
import pandas as pd
from typing import Dict
from canoe_agriculture.common import setup_logging

logger = setup_logging()

ATL_MAP = { 'PEI': 'Prince Edward Island', 'NS': 'Nova Scotia', 'NB': 'New Brunswick', 'NLLAB': 'Newfoundland and Labrador' }
SECTOR_KEY = 'Agriculture, fishing, hunting and trapping'


def _gdp_scalers(pop_df: pd.DataFrame, periods: list[int]) -> dict[int, float]:
    df = pop_df.copy()
    df = df[df['Year'].isin(periods)]
    df = df[df['Variable'] == 'Real Gross Domestic Product ($2012 Millions)']
    df = df[df['Scenario'] == 'Global Net-zero']
    df = df.sort_values('Year').set_index('Year')['Value']
    df = df / df.iloc[0]
    return df.to_dict()


def _atl_split(val: float, province: str, shares: dict[str, dict[str, float]]) -> float | None:
    if province not in ATL_MAP: return None
    try:
        return float(val) * float(shares[SECTOR_KEY][ATL_MAP[province]])
    except Exception:
        return None


def build_demand_and_capacity_agri(
    comb_dict: Dict[str, pd.DataFrame],
    loaded_df: dict[str, pd.DataFrame],
    pop_df: pd.DataFrame,
    atl_shares: dict[str, dict[str, float]],
) -> Dict[str, pd.DataFrame]:
    dom = comb_dict['__domain__']; ids = comb_dict['__ids__']
    sector_abv = dom['sector_abv']; province_list = dom['province_list']
    sector_list = dom['sector_list']; periods = dom['periods']; atl_pro = set(dom['atl_pro'])
    demand_com_list = comb_dict.get('__demand_com_list__', ['D_AGRI'])

    gdp_scale = _gdp_scalers(pop_df, periods)

    # Base values from NRCan table (first row index 0 as in original)
    base2022 = {p: float(loaded_df['ATL']['2022'][0]) if p in atl_pro else float(loaded_df[p]['2022'][0]) for p in province_list}

    # Demand rows
    d_rows = []
    for pro in province_list:
        for year in periods:
            for dem in demand_com_list:
                if year == min(periods):
                    notes, ref = 'Value from NRCan Comprehensive DB', 'A1'
                    val = base2022[pro]
                    if pro in atl_pro:
                        split = _atl_split(val, pro, atl_shares)
                        if split is None: continue
                        val, ref = split, 'A3'
                else:
                    notes, ref = 'Scaled by GDP growth from CER CEF', 'A2'
                    val = base2022[pro] * gdp_scale[year]
                    if pro in atl_pro:
                        split = _atl_split(base2022[pro], pro, atl_shares)
                        if split is None: continue
                        val, ref = float(split) * gdp_scale[year], 'A4'

                d_rows.append([
                    pro, int(year), sector_abv + dem.lower(), float(val), 'PJ', notes, ref, 1,1,2,3,2, ids[pro]
                ])

    demand_df = pd.DataFrame(d_rows, columns=comb_dict['Demand'].columns)
    comb_dict['Demand'] = pd.concat([comb_dict['Demand'], demand_df], ignore_index=True)
    logger.info("Demand rows: %d", len(d_rows))

    # ExistingCapacity from 2021 baseline
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