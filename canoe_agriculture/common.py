# -*- coding: utf-8 -*-
"""
Created on Fri Sep 26 08:48:03 2025

@author: david
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Literal

from canoe_schema.v4_0.models import CommodityTypeCode
from pydantic import BaseModel, ConfigDict, field_validator

LOGGER_NAME = "agri_etl"


class CANOEInputFuel(BaseModel):
    shortname: str
    longname: str
    nrcan_row_idx: int
    commodity_type: CommodityTypeCode = CommodityTypeCode.A


class CANOEAgricultureConfig(BaseModel):
    # No additional fields are allowed
    model_config = ConfigDict(extra="forbid")

    # Fields that may be pushed up to a common config
    schema_version: str = "3.1"
    db_dir: Path = Path("CAN_agriculture.sqlite")
    existing_periods: list[int]
    future_periods: list[int]
    # TODO replace with CANOEProvince class
    province_list: list[str]
    validation_behavior: Literal["error", "warning"] = "error"

    # Data-related fields
    version: str = "001"
    NRCan_year: int = 2022

    # Sector configuration
    sector_initial: str = "A"
    sector_abv: str = "AGRI"
    sector_longname: str = "Agriculture"
    input_fuels: list[CANOEInputFuel]
    remainder_fuel_limit_tech_annual: str

    @classmethod
    def validate_from_toml(cls, toml_dir: str) -> CANOEAgricultureConfig:
        with Path(toml_dir).open("rb") as f:
            return CANOEAgricultureConfig.model_validate(tomllib.load(f))

    @field_validator("db_dir")
    @classmethod
    def expand_path(cls, v: Path) -> Path:
        return v.expanduser()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def project_paths() -> dict[str, Path]:
    root = Path.cwd()
    return {
        "root": root,
        "input": root / "input",
        "outputs": root / "outputs",
        "cache": root / "cache",
        "schema": root / "schema",
    }
