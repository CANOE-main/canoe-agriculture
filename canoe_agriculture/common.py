# -*- coding: utf-8 -*-
"""
Created on Fri Sep 26 08:48:03 2025

@author: david
"""

from __future__ import annotations
import logging
from pathlib import Path
import tomllib
from typing import Any, Dict, Literal
import yaml
from pydantic import BaseModel, ConfigDict

LOGGER_NAME = "agri_etl"


class CANOEInputFuel(BaseModel):
    shortname: str
    longname: str
    nrcan_row_idx: int


class CANOEAgricultureConfig(BaseModel):
    # No additional fields are allowed
    model_config = ConfigDict(extra="forbid")

    # Fields that may be pushed up to a common config
    schema_version: str = "3.1"
    db_dir: str = "CAN_agriculture.sqlite"
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


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        logger.setLevel(level)
        handler = logging.StreamHandler()
        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    return logger


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
