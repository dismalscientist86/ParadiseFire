"""
Configuration file for Paradise Fire analysis.
Sets paths and constants used across all scripts.
"""
import os
from pathlib import Path

# Base directories - adjust ROOT_DIR as needed for your machine
# Code lives in Dropbox, data stored on M: drive to save space
CODE_DIR = Path(__file__).parent.parent.parent
DATA_ROOT = Path("M:/ParadiseFire")

ANALYSIS_DIR = CODE_DIR / "Analysis"
DATA_DIR = DATA_ROOT / "data"
GRAPHS_DIR = ANALYSIS_DIR / "graphs"
TABLES_DIR = ANALYSIS_DIR / "tables"
PYTHON_DIR = ANALYSIS_DIR / "python"

# Create directories if they don't exist
for dir_path in [DATA_DIR, GRAPHS_DIR, TABLES_DIR,
                 DATA_DIR / "lodes_od", DATA_DIR / "lodes_rac", DATA_DIR / "lodes_wac"]:
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass  # May fail if drive not mounted; will error at runtime if needed

# LODES data URL base
LODES_BASE_URL = "https://lehd.ces.census.gov/data/lodes/LODES8/ca"

# Geographic constants
BUTTE_COUNTY_FIPS = "06007"

# Paradise census tracts (2020 geography - tracts 18, 19, 20, 21 in Butte County)
# LODES8 uses 2020 census blocks with 11-digit tract codes
PARADISE_TRACTS = ["06007001800", "06007001900", "06007002000", "06007002100"]

# Data years
YEARS = list(range(2013, 2024))  # 2013-2023

# Job types
JOB_TYPES = ["JT00"]  # All jobs; can add JT01-JT05 for specific job types

# LODES variable descriptions
LODES_VARS = {
    "c000": "Total jobs",
    "ca01": "Age 29 or younger",
    "ca02": "Age 30-54",
    "ca03": "Age 55+",
    "ce01": "Earnings $1,250/month or less",
    "ce02": "Earnings $1,251-$3,333/month",
    "ce03": "Earnings more than $3,333/month",
    "cns01": "Agriculture, Forestry, Fishing, Hunting",
    "cns02": "Mining, Quarrying, Oil/Gas",
    "cns03": "Utilities",
    "cns04": "Construction",
    "cns05": "Manufacturing",
    "cns06": "Wholesale Trade",
    "cns07": "Retail Trade",
    "cns08": "Transportation, Warehousing",
    "cns09": "Information",
    "cns10": "Finance, Insurance",
    "cns11": "Real Estate",
    "cns12": "Professional, Scientific, Technical",
    "cns13": "Management",
    "cns14": "Admin, Support, Waste Management",
    "cns15": "Educational Services",
    "cns16": "Health Care, Social Assistance",
    "cns17": "Arts, Entertainment, Recreation",
    "cns18": "Accommodation, Food Services",
    "cns19": "Other Services",
    "cns20": "Public Administration",
    "cr01": "White Alone",
    "cr02": "Black or African American Alone",
    "cr03": "American Indian or Alaska Native Alone",
    "cr04": "Asian Alone",
    "cr05": "Native Hawaiian or Pacific Islander Alone",
    "cr07": "Two or More Races",
    "ct01": "Not Hispanic or Latino",
    "ct02": "Hispanic or Latino",
    "cd01": "Less than high school",
    "cd02": "High school or equivalent",
    "cd03": "Some college or Associate degree",
    "cd04": "Bachelor's degree or higher",
    "cs01": "Male",
    "cs02": "Female",
}

# Top 6 industries for focused analysis
TOP_INDUSTRIES = ["cns04", "cns07", "cns15", "cns16", "cns18", "cns20"]
TOP_INDUSTRY_NAMES = {
    "cns04": "Construction",
    "cns07": "Retail Trade",
    "cns15": "Educational Services",
    "cns16": "Health Care",
    "cns18": "Accommodation & Food",
    "cns20": "Public Administration",
}
