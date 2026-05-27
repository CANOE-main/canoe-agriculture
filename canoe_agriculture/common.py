# -*- coding: utf-8 -*-
"""
Created on Fri Sep 26 08:48:03 2025

@author: david
"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Any, Dict
import yaml

LOGGER_NAME = "agri_etl"

class Config:
    def __init__(self, params: dict):
        self.params = params
    @property
    def schema_version(self) -> int:
        v = self.params.get("schema_version", [31])[0]
        return int(v)
    @property
    def version(self) -> str:
        v = self.params.get("version", "1")
        return f"{int(v):03d}"  # "001", "012", "123"
    @property
    def periods(self) -> list[int]:
        return list(self.params.get("periods", [2025]))
    @property
    def nrcan_year(self) -> int:
        return int(self.params.get("NRCan_year", 2022))
    @property
    def db_name(self) -> Path:
        return Path(self.params.get("db_name", "CAN_agriculture.sqlite"))

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


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def project_paths() -> dict[str, Path]:
    root = Path.cwd()
    return {"root": root, "input": root / "input", "outputs": root / "outputs", "cache": root / "cache", "schema": root / "schema"}