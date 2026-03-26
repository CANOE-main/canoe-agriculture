# Agriculture ETL Pipeline (with Atlantic Split)

A production-ready, modular ETL pipeline that builds the **Agriculture** sector tables for the CANOE database.  
It integrates **NRCan** (Comprehensive Energy Use Database) and **CER** (Energy Futures macro indicators) data, and allocates **Atlantic provinces** (PEI, NB, NS, NLLAB) using **Statistics Canada Table 25-10-0029-01** shares.

Please visit [here](https://canoe-main.github.io/canoe-agriculture/) for information regarding the agriculture sector.

> This README documents the `src/*_agri.py` modules produced in the refactor.

---

## Table of Contents
- [Overview](#overview)
- [Project Layout](#project-layout)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration (`params.yaml`)](#configuration-paramsyaml)
- [Data Sources](#data-sources)
- [What the Pipeline Builds](#what-the-pipeline-builds)
- [Logging](#logging)
- [Re-running & Caching](#re-running--caching)
- [Troubleshooting](#troubleshooting)
- [Extending / Customization](#extending--customization)
- [Reproducibility Notes](#reproducibility-notes)

---

## Overview

The pipeline orchestrates these steps:

1. **Setup**: Create a fresh SQLite database from your schema, and introspect table structures to prepare empty DataFrames (`comb_dict`).  
2. **Technology & Commodity**: Add Agriculture technology and commodity scaffolding, including demand commodities.  
3. **External Data**: Fetch or load cached **NRCan** (Agriculture) and **CER** (macro indicators) data.  
4. **Atlantic Shares (StatCan)**: Load ATL shares to distribute Atlantic aggregate values to **PEI, NB, NS, NLLAB**.  
5. **Demand & ExistingCapacity**:  
   - Base year from NRCan (e.g., 2025 uses 2022 NRCan values by default).  
   - Subsequent years scaled by **CER GDP growth**.  
   - ATL provinces receive values split according to StatCan shares.  
6. **LimitTechInputSplitAnnual**: Compute commodity input shares; handle `n.a.`/`X` as remainder-to-100% and trim any >100%.  
7. **Efficiency**: Derive from `LimitTechInputSplitAnnual` (efficiency=1), mapping `tech` → `output_comm` (`A_d_*`).  
8. **Costs**: Seed `CostInvest` (placeholder values).  
9. **Post-processing**: Add `DataSet` and `DataSource` metadata rows.  
10. **Persist**: Write all DataFrames to the SQLite database.

---

## Project Layout

```
project/
├─ input/
│  └─ params.yaml
├─ outputs/
├─ cache/
├─ schema/
│  └─ schema_3_1.sql              # or schema_{X}.sql per params.yaml
├─ common.py
├─ setup_agri.py
├─ techcom_agri.py
├─ data_scraper_agri.py
├─ statcan_agri.py
├─ demands_agri.py
├─ costs_agri.py
├─ techinput_agri.py
├─ efficiency_agri.py
├─ post_processing_agri.py
└─ requirements.txt
```

> The main entry point is `aggregator_agri.py` (if present in your repo).

---

## Prerequisites

- **Python 3.10+**
- Packages (install via `requirements.txt`):
  - `pandas`
  - `pyyaml`
  - `requests`

```bash
pip install -r requirements.txt
```

---

## Quick Start

1. **Configure** `input/params.yaml` (see example below).  
2. Ensure your **schema** file exists in `schema/` (e.g., `schema_3_1.sql`).  
3. Run the aggregator:

```bash
# from project root
python aggregator_agri.py --db-name CAN_agriculture.sqlite
```

- Output database is written to: `outputs/CAN_agriculture.sqlite`.

---

## Configuration (`params.yaml`)

Minimal example:

```yaml
version: 1                        # used for DataSet IDs (e.g., AGRIHRAB1)
schema_version: [31]              # maps to schema file schema_3_1.sql
periods: [2025, 2030, 2035]       # model years to build
NRCan_year: 2022                  # base year for NRCan pulls
```

- **version**: increments dataset/data_id versions.
- **schema_version**: selects the SQL schema file:
  - if `31`, uses `schema_3_1.sql`
  - otherwise, uses `schema_{schema_version}.sql`
- **periods**: first period is treated as the **base**; later years are **scaled** by CER GDP growth.
- **NRCan_year**: NRCan table year to fetch (Agriculture sector, `rn=1`).

---

## Data Sources

- **NRCan CEUD** (Comprehensive Energy Use Database) — Agriculture tables by province and **ATL** aggregate.
  - Used for base-year demand and input shares.
- **CER Energy Futures** (Macro Indicators 2023) — GDP series for **Global Net-zero** scenario.
  - Used as **scaling factors** between periods.
- **Statistics Canada** Table **25-10-0029-01**
  - Used to create **Atlantic shares** that split ATL aggregates into **PEI, NB, NS, NLLAB**.

> All downloads are cached in `cache/` to speed up re-runs and reduce web requests.

---

## What the Pipeline Builds

Tables written to SQLite (subject to your schema definition):

- `Technology` — agriculture technology records.
- `Commodity` — agriculture commodity records, plus demand commodity for the sector.
- `Demand` — demand time series, base from NRCan, scaled by CER GDP in later years; ATL split by StatCan.
- `ExistingCapacity` — baseline (e.g., 2021) per sector/province; ATL split by StatCan.
- `LimitTechInputSplitAnnual` — commodity input shares; handles `n.a.`/`X` and >100% trims.
- `Efficiency` — derived from techinput with efficiency=1 and `output_comm` mapped from `tech`.
- `CostInvest` — seeded placeholder cost values.
- `DataSet`/`DataSource` — metadata rows (with `[A1]` NRCan, `[A2]` CER, `[A3]` StatCan).

---

## Logging

A simple stream logger is configured in `common.py`:
- Format: `YYYY-MM-DD HH:MM:SS | LEVEL | logger | message`
- You can tune the level by editing `setup_logging()` in `common.py`.

---

## Re-running & Caching

- The **database** is recreated on each run (existing DB with same name is removed before schema is applied).
- The **web data cache** in `cache/` persists across runs:
  - `dataframes.pkl` — NRCan tables
  - `pop_df.pkl` — CER macro indicators
  - `statcan_agri.pkl` — StatCan ATL shares
- Delete files in `cache/` to force fresh downloads.

---

## Troubleshooting

**Common issues**

1. **Schema mismatch / missing columns**  
   - Ensure the schema file matches the expected table columns for your ETL (e.g., `schema_3_1.sql`).  
   - Fix by updating the schema file or the ETL column mappings.

2. **HTTP/Parsing errors** (NRCan/CER/StatCan)  
   - Check internet connectivity.  
   - Source pages may change; adjust parsers or mappings if columns move.

3. **Empty tables written**  
   - The aggregator skips empty DataFrames.  
   - Inspect logs to verify which steps produced rows.

4. **Atlantic allocation seems off**  
   - Confirm `statcan_agri.pkl` has non-zero shares for 2023.  
   - Validate that the sector label used for ATL (`Agriculture, fishing, hunting and trapping`) exists in the CSV and is filtered correctly.

---

## Extending / Customization

- **Parameterize mappings**: move `COM_TO_COL` or sector labels into YAML.
- **Add sectors**: mirror the builder functions and include them in the aggregator flow.
- **Unit tests**: create tests for GDP scaling, ATL shares, and NA/share-trimming logic.
- **CLI options**: expose more args (e.g., `--force-download`, custom cache dir).

---

## Reproducibility Notes

- Inputs:
  - `params.yaml` (controls model periods, NRCan year, schema selection)
  - Remote sources (NRCan, CER, StatCan); cached locally
- Pipeline is **deterministic** given cached inputs and fixed schema.
- The first **period** acts as base; later periods are scaled by **CER GDP** ratios.
- **Atlantic provinces** are derived by splitting the ATL region using **StatCan 25-10-0029-01** shares for 2023.
