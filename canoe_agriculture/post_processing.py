# -*- coding: utf-8 -*-
"""
Created on Sun Aug 17 13:04:16 2025

@author: david
"""

from __future__ import annotations
from sqlite3 import Cursor
from typing import Dict
import pandas as pd
from loguru import logger
from canoe_schema.v4_0.models import (
    DataSet,
    DataSource
)


def add_datasets_and_sources_agri(
        db_cursor: Cursor,
    comb_dict: Dict[str, pd.DataFrame],
) -> Dict[str, pd.DataFrame]:
    dom = comb_dict["__domain__"]
    ids = comb_dict["__ids__"]
    province_list = dom["province_list"]
    version = comb_dict["__version__"]

    ds_rows = []
    for pro in province_list:
        ds_rows.append(
            DataSet(
                data_id=ids[pro],
                label=f"{pro} - Agriculture - high resolution",
                version=f"v{version}",
                description="2025 annual update",
                status="active",
                author="David Turnbull - david.turnbull1@ucalgary.ca",
                date="2025-08-01",
                changelog="Original sector design",
            )
        )
    ds_rows.append(
        DataSet(
            data_id=ids["CAN"],
            label="General Agriculture - high resolution",
            version=f"v{version}",
            description="2025 annual update",
            status="active",
            author="David Turnbull - david.turnbull1@ucalgary.ca",
            date="2025-08-01",
            changelog="Original sector design",
        )
    )
    db_cursor.executemany(*DataSet.bulk_insert_or_ignore_sql(ds_rows))

    src_rows = [
        [
            "A1",
            "NRCan Comprehensive Database, https://oee.nrcan.gc.ca/corporate/statistics/neud/dpa/menus/trends/comprehensive_tables/list.cfm",
            "Used the appropriate tables for each sector and province",
            ids["CAN"],
        ],
        [
            "A2",
            "NRCan Comprehensive Database, https://oee.nrcan.gc.ca/corporate/statistics/neud/dpa/menus/trends/comprehensive_tables/list.cfm; Canada Energy Regulator Canada Energy Futures report, https://apps.cer-rec.gc.ca/ftrppndc/dflt.aspx?GoCTemplateCulture=en-CA",
            "Global net zero macro-economics indicators",
            ids["CAN"],
        ],
        [
            "A3",
            "NRCan Comprehensive Database, https://oee.nrcan.gc.ca/corporate/statistics/neud/dpa/menus/trends/comprehensive_tables/list.cfm; Statistics Canada 25-10-0029-01, https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2510002901",
            "Used presence/values to dictate sector presence in ATL",
            ids["CAN"],
        ],
        [
            "A4",
            "NRCan Comprehensive Database, https://oee.nrcan.gc.ca/corporate/statistics/neud/dpa/menus/trends/comprehensive_tables/list.cfm; Canada Energy Regulator Canada Energy Futures report, https://apps.cer-rec.gc.ca/ftrppndc/dflt.aspx?GoCTemplateCulture=en-CA;Statistics Canada 25-10-0029-01, https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2510002901",
            "Combined reference to utilize GDP growth, NRCan demand values and statcan atlantic province distribution",
            ids["CAN"],
        ],
    ]
    dssrc_rows = []
    for row in src_rows:
        dssrc_rows.append(
            DataSource(source_id=row[0], source=row[1], notes=row[2], data_id=row[3])
        )
    db_cursor.executemany(*DataSource.bulk_insert_or_ignore_sql(dssrc_rows))
    logger.info(
        f"Post-processing: {len(ds_rows)} DataSet, {len(dssrc_rows)} DataSource"
    )
