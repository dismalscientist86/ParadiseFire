# -*- coding: utf-8 -*-
"""
Legacy data download and processing script.
Replaced by 01_download_data.py and 02_extract_process.py
"""

import os
import requests
import gzip
import shutil
import pandas as pd
import glob


# Define a function to download and read the data from the URL
def download_data(url, file_path, dtype):
    # Download the file from the URL
    response = requests.get(url, stream=True)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(response.raw, f)

    # Unzip the file and save it as a CSV file
    with gzip.open(file_path, "rb") as f_in:
        with open(os.path.splitext(file_path)[0], "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    # Read the CSV file and return the data frame
    df = pd.read_csv(file_path, dtype=dtype)
    return df


# Define the base directory for the project
# UPDATE THIS PATH for your machine:
base_dir = os.path.join(os.path.dirname(__file__), "..", "..")

# Define the subdirectories for programs, data, output, logs, and graphs
programs = os.path.join(base_dir, "programs")
data = os.path.join(base_dir, "data")
output = base_dir
logs = os.path.join(programs, "logs")
graphs = os.path.join(base_dir, "graphs")
data_od = os.path.join(data, "lodes_od")
data_rac = os.path.join(data, "lodes_rac")
data_wac = os.path.join(data, "lodes_wac")

# Bring in Origin-Destination Main dataset, for All Jobs (JT00)
for i in range(2013, 2021):
    url = f"https://lehd.ces.census.gov/data/lodes/LODES8/ca/od/ca_od_main_JT00_{i}.csv.gz"
    file_path = os.path.join(data_od, f"ca_od_main_JT00_{i}.csv.gz")

    # Use the function to download and read the data
    od_data = download_data(url, file_path, dtype=str)

    # Create county FIPS from first five digits of geocode
    od_data["w_county"] = od_data["w_geocode"].str[:5]
    od_data["w_tract"] = od_data["w_geocode"].str[:9]
    od_data["h_county"] = od_data["h_geocode"].str[:5]
    od_data["h_tract"] = od_data["h_geocode"].str[:9]

    # Keep only Butte County (FIPS=06007)
    od_data = od_data[od_data["w_county"].isin(["06007"]) | od_data["h_county"].isin(["06007"])]

    # Save resulting data as CSV file
    od_data.to_csv(os.path.join(data_od, f"od_main_JT00_{i}.csv"), index=False)

# Bring in Residence Area Characteristics Main dataset, for All Jobs (JT00)
for i in range(2013, 2021):
    url = f"https://lehd.ces.census.gov/data/lodes/LODES8/ca/rac/ca_rac_S000_JT00_{i}.csv.gz"
    file_path = os.path.join(data_rac, f"ca_rac_S000_JT00_{i}.csv.gz")

    # Use the function to download and read the data
    rac_data = download_data(url, file_path, dtype=str)

    # Create county FIPS from first five digits of geocode
    rac_data["h_county"] = rac_data["h_geocode"].str[:5]
    rac_data["h_tract"] = rac_data["h_geocode"].str[:9]

    # Keep only Butte County (FIPS=06007)
    rac_data = rac_data[rac_data["h_county"].isin(["06007"])]

    # Save resulting data as CSV file
    rac_data.to_csv(os.path.join(data_rac, f"rac_S000_JT00_{i}.csv"), index=False)

# Bring in Work Area Characteristics Main dataset, for All Jobs (JT00)
for i in range(2013, 2021):
    url = f"https://lehd.ces.census.gov/data/lodes/LODES8/ca/wac/ca_wac_S000_JT00_{i}.csv.gz"
    file_path = os.path.join(data_wac, f"ca_wac_S000_JT00_{i}.csv.gz")

    # Use the function to download and read the data
    wac_data = download_data(url, file_path, dtype=str)

    # Create county FIPS from first five digits of geocode
    wac_data["w_county"] = wac_data["w_geocode"].str[:5]
    wac_data["w_tract"] = wac_data["w_geocode"].str[:9]

    # Keep only Butte County (FIPS=06007)
    wac_data = wac_data[wac_data["w_county"].isin(["06007"])]

    # Save resulting data as CSV file
    wac_data.to_csv(os.path.join(data_wac, f"wac_S000_JT00_{i}.csv"), index=False)

# Append data from years 2013-2020 and flag Paradise geocodes
# Origin-Destination
files = glob.glob(os.path.join(data_od, "od_main_JT00_*.csv"))
od_df = pd.DataFrame()

for file in files:
    od_year = pd.read_csv(file, dtype=str)
    year = file.split("_")[-1].split(".")[0]
    od_year['year'] = year
    od_df = pd.concat([od_df, od_year], ignore_index=True)

paradise_tracts = ["060070018", "060070019", "060070020", "060070021"]
od_df['paradise'] = od_df['h_tract'].apply(lambda x: 1 if x in paradise_tracts else 0) | od_df['w_tract'].apply(lambda x: 1 if x in paradise_tracts else 0)
od_df.to_csv(os.path.join(data, "od_2013_2020.csv"))

# Work Area Characteristics
files = glob.glob(os.path.join(data_wac, "wac_S000_JT00_*.csv"))
wac_df = pd.DataFrame()

for file in files:
    wac_year = pd.read_csv(file, dtype=str)
    year = file.split("_")[-1].split(".")[0]
    wac_year['year'] = year
    wac_df = pd.concat([wac_df, wac_year], ignore_index=True)

wac_df['paradise'] = wac_df['w_tract'].apply(lambda x: 1 if x in paradise_tracts else 0)
freq_table = wac_df['paradise'].value_counts()
print(freq_table)
wac_df.to_csv(os.path.join(data, "wac_2013_2020.csv"))

# Residence Area Characteristics
files = glob.glob(os.path.join(data_rac, "rac_S000_JT00_*.csv"))
rac_df = pd.DataFrame()

for file in files:
    rac_year = pd.read_csv(file, dtype=str)
    year = file.split("_")[-1].split(".")[0]
    rac_year['year'] = year
    rac_df = pd.concat([rac_df, rac_year], ignore_index=True)

rac_df['paradise'] = rac_df['h_tract'].apply(lambda x: 1 if x in paradise_tracts else 0)
freq_table = rac_df['paradise'].value_counts()
print(freq_table)
rac_df.to_csv(os.path.join(data, "rac_2013_2020.csv"))
