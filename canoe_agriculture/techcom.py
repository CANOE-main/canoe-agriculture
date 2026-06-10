# -*- coding: utf-8 -*-
"""
Created on Fri Aug 15 08:34:22 2025

@author: david
"""

from __future__ import annotations
from sqlite3 import Cursor
import pandas as pd
from typing import Dict
from loguru import logger
from canoe_schema.v4_0.models import Commodity, Technology, Commodity
from canoe_agriculture.common import CANOEAgricultureConfig


def add_technology_and_fuel_commodities(
    module_config: CANOEAgricultureConfig,
    db_cursor: Cursor,
    data_id_code: str,
) -> Dict[str, pd.DataFrame]:
    """
    Add Agriculture technology and fuel technologies
    """

    # Add technology that represents the sector
    tech_sql, tech_params = Technology(
        tech=f"{module_config.sector_initial}_{module_config.sector_abv}",
        flag="p",
        sector="agriculture",  # TODO Consider defining the sectors in a shared collection
        unlim_cap=1,
        annual=1,
        # NOTE: The rest of the flags are 0 by default
        description=f"Generic technology representing {module_config.sector_longname}",
        data_id=data_id_code,
    ).to_insert_or_ignore_sql()
    db_cursor.execute(tech_sql, tech_params)

    # Add the demand commodity
    demand_sql, demand_params = Commodity(
        name=f"{module_config.sector_initial}_d_{module_config.sector_abv.lower()}",
        flag="d",
        description=f"Demand for the {module_config.sector_longname} sector",
        units=None,  # TODO What do we do with the new units?
        data_id=data_id_code,
    ).to_insert_or_ignore_sql()
    db_cursor.execute(demand_sql, demand_params)

    # Add the fuels that represent input commodities
    comm_rows = []
    for input_commodity in module_config.input_fuels:
        comm_rows.append(
            Commodity(
                name=f"{module_config.sector_initial}_{input_commodity.shortname}",
                flag="a",
                description=f"Represents {input_commodity.longname} in the agriculture sector",
                data_id=data_id_code,
            )
        )
    db_cursor.executemany(*Commodity.bulk_insert_or_ignore_sql(comm_rows))

    logger.info(f"Technology rows: 1, Commodity rows: {len(comm_rows) + 1}")
