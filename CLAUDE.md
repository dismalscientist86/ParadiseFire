# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Research project studying the economic impacts of the 2018 Camp Fire on Paradise, California using LODES (Longitudinal Employer-Household Dynamics Origin-Destination Employment Statistics) data from the U.S. Census Bureau.

## Running the Analysis

All code is in Stata (.do files). Programs should be run in numerical order:

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
- Paradise census tracts: 060070018, 060070019, 060070020, 060070021
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

## Path Configuration

`00_master_setup.do` sets global macros based on `c(username)`:
- `sandl305` (Dani Sandler): Uses `C:\Users\sandl305\Documents\GitHub\ParadiseFire\`
- Others (Gabriela Lahera): Uses `C:\Users\Gabriela.Lahera\Documents\GitHub\ParadiseFire\`

To add a new user, add a conditional block in `00_master_setup.do`.

## Methodology

The project uses difference-in-differences analysis comparing Paradise to the rest of Butte County, with the fire (November 2018) as the treatment event. Control variables include 2017 baseline levels of prime-age workers, education, and gender composition.
