# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Research project studying the economic impacts of the 2018 Camp Fire on Paradise, California using LODES (Longitudinal Employer-Household Dynamics Origin-Destination Employment Statistics) data from the U.S. Census Bureau.

## Directory Structure

```
ParadiseFire/
├── Analysis/
│   ├── data/           # Migration data, tract maps, supporting data
│   ├── graphs/         # Generated visualizations (PNG, JPG)
│   ├── programs/       # Stata do-files (legacy)
│   ├── python/         # Python analysis scripts (recommended)
│   └── tables/         # Output tables (CSV)
├── GoogleEarth/        # Satellite imagery (Sept 2018, Dec 2018, May 2023)
├── Notes/              # Project documentation
└── Writeup/            # Paper/manuscript materials
```

**Data storage:** Code lives in Dropbox, but LODES data is stored on `M:/ParadiseFire/` to save space. See `config.py` for path configuration.

## Running the Analysis (Python - Recommended)

Python scripts are in `Analysis/python/`. Install dependencies and run the full pipeline:

```bash
cd Analysis/python
pip install -r requirements.txt

# Full pipeline (download, process, analyze, visualize)
python run_analysis.py --all

# Or run individual steps:
python 01_download_data.py                    # Download LODES data (2013-2023)
python 02_extract_process.py                  # Extract Butte County, identify Paradise
python 03_analysis.py --data wac              # Run diff-in-diff regressions
python 04_visualizations.py                   # Generate all plots

# Synthetic control analysis
python 05_synthetic_control.py --data wac     # Run synthetic control method
python 05_synthetic_control.py --placebo      # Run placebo tests
python 05_synthetic_control.py --placebo --exclude-2020  # Placebo tests excluding COVID year
```

**Key Python files:**
- `config.py`: Paths, constants, LODES variable definitions (edit `DATA_ROOT` for your machine)
- `01_download_data.py`: Downloads raw LODES CSVs from Census Bureau
- `02_extract_process.py`: Extracts Butte County, creates Paradise indicator
- `03_analysis.py`: Aggregation and difference-in-differences regression
- `04_visualizations.py`: Bar charts, trend lines, percent change plots
- `05_synthetic_control.py`: Synthetic control method with placebo tests
- `run_analysis.py`: Pipeline orchestrator (supports `--all`, `--download`, `--process`, `--analyze`, `--visualize`)

**Other Python utilities:**
- `readIn_migration.py`, `readIn_SOImigration.py`: Migration data processing
- `01_readIn_data.py`, `02_residentialarea_graphs.py`, `03_workarea_graphs.py`: Alternative/legacy scripts

**Dependencies:** pandas, numpy, requests, matplotlib, seaborn, statsmodels, pyarrow, scipy

## Running the Analysis (Stata - Legacy)

Original Stata code is in `Analysis/programs/`. Run in numerical order:

```stata
do 00_master_setup.do       # Sets up file paths (run first, or included by other scripts)
do 02_extract_ButteCo.do    # Extract Butte County from LODES CSVs, save as .dta
do 03_residence_area.do     # Process RAC (Residence Area Characteristics) data
do 04_work_area.do          # Process WAC (Work Area Characteristics) data
do 05_Bar_graphs_subgroups.do   # Generate bar graphs by demographic subgroups
do 06_Percent_change.do     # Generate percent change graphs
do 07_difference_in_difference.do  # Run diff-in-diff regressions
```

## Key Data Concepts

**Geographic identifiers:**
- Paradise census tracts (11-digit): 06007001800, 06007001900, 06007002000, 06007002100
- Butte County FIPS: 06007
- The `paradise` dummy variable = 1 for Paradise tracts, 0 for rest of Butte County

**LODES data types:**
- **OD (Origin-Destination)**: Where workers live and work
- **RAC (Residence Area Characteristics)**: Worker characteristics by home location (`h_geocode`)
- **WAC (Work Area Characteristics)**: Job characteristics by workplace location (`w_geocode`)

**Variable prefixes in LODES:**
- `c000`: Total jobs
- `ca01-ca03`: Age groups (29 and younger, 30-54, 55+)
- `ce01-ce03`: Earnings ($1,250 or less, $1,251-$3,333, more than $3,333)
- `cns01-cns20`: Industry sectors (NAICS 2-digit)
- `cr01-cr07`: Race categories
- `ct01-ct02`: Ethnicity (Not Hispanic, Hispanic)
- `cd01-cd04`: Educational attainment
- `cs01-cs02`: Sex (Male, Female)

**Top 6 industries for focused analysis:** Construction, Retail Trade, Educational Services, Health Care, Accommodation & Food, Public Administration

## Path Configuration

**Python executable:** `/c/Users/Sandler/anaconda3/python.exe` (Anaconda installation)

**Python (`config.py`):**
- `CODE_DIR`: Auto-detected from script location (Dropbox)
- `DATA_ROOT`: Set to `M:/ParadiseFire` (large data files stored externally)
- Adjust `DATA_ROOT` if running on a different machine

**Stata (`00_master_setup.do`):**
Sets global macros based on `c(username)`:
- `sandl305` (Dani Sandler): Uses `C:\Users\sandl305\Documents\GitHub\ParadiseFire\`
- Others (Gabriela Lahera): Uses `C:\Users\Gabriela.Lahera\Documents\GitHub\ParadiseFire\`

To add a new user, add a conditional block in `00_master_setup.do`.

## Methodology

**Difference-in-Differences:** Compares Paradise to the rest of Butte County, with the fire (November 2018) as the treatment event. Control variables include 2017 baseline levels of prime-age workers, education, and gender composition.

**Synthetic Control:** Creates a weighted combination of other California tracts that best match Paradise's pre-fire employment trends. Excludes Butte County donors to avoid spillover effects. Includes placebo tests for statistical inference.
