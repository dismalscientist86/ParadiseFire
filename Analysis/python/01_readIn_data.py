import os
import requests
import gzip
import shutil
import pandas as pd

if os.getlogin() == "sandl305":
    programs = r"C:\\Users\\sandl305\\Documents\\GitHub\\ParadiseFire\\Analysis\\programs"
    data = r"C:\\Users\\sandl305\\Documents\\GitHub\\ParadiseFire\\Analysis\\data"
    output = r"C:\\Users\\sandl305\\Documents\\GitHub\\ParadiseFire\\Analysis"
    logs = r"C:\\Users\\sandl305\\Documents\\GitHub\\ParadiseFire\\Analysis\\programs\\logs"
    graphs = r"C:\\Users\\sandl305\\Documents\\GitHub\\ParadiseFire\\Analysis\\graphs"
    data_od = r"C:\\Users\\sandl305\\Documents\\GitHub\\ParadiseFire\\Analysis\\data\\lodes_od"
    data_rac = r"C:\\Users\\sandl305\\Documents\\GitHub\\ParadiseFire\\Analysis\\data\\lodes_rac"
    data_wac = r"C:\\Users\\sandl305\\Documents\\GitHub\\ParadiseFire\\Analysis\\data\\lodes_wac"

# Download and process Origin-Destination Main dataset (2013-2020)
for i in range(2013, 2021):
    url = f"https://lehd.ces.census.gov/data/lodes/LODES8/ca/od/ca_od_main_JT00_{i}.csv.gz"
    file_path = os.path.join(data_od, f"ca_od_main_JT00_{i}.csv.gz")

    response = requests.get(url, stream=True)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(response.raw, f)

    with gzip.open(file_path, "rb") as f_in:
        with open(os.path.splitext(file_path)[0], "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    # Read and filter CSV file
    df = pd.read_csv(os.path.splitext(file_path)[0], dtype=str)
    df["w_county"] = df["w_geocode"].str[:5]
    df["w_tract"] = df["w_geocode"].str[:9]
    df["h_county"] = df["h_geocode"].str[:5]
    df["h_tract"] = df["h_geocode"].str[:9]
    df = df[(df["w_county"] == "06007") | (df["h_county"] == "06007")]

    # Save processed file
    df.to_csv(os.path.join(data_od, f"od_main_JT00_{i}.csv"), index=False)

# Append data and flag Paradise geocodes
od_df = pd.read_csv(os.path.join(data_od, 'od_main_JT00_2013.csv'), dtype=str)
od_df['year'] = 2013

for year in range(2014, 2021):
    od_year = pd.read_csv(os.path.join(data_od, f'od_main_JT00_{year}.csv'), dtype=str)
    od_year['year'] = year
    od_df = pd.concat([od_df, od_year], ignore_index=True)

od_df['paradise'] = 0
paradise_tracts = ["060070018", "060070019", "060070020", "060070021"]
od_df.loc[od_df['h_tract'].isin(paradise_tracts), 'paradise'] = 1
od_df.loc[od_df['w_tract'].isin(paradise_tracts), 'paradise'] = 1

od_df.to_csv(os.path.join(data, "od_2013_2020.csv"), index=False)

# Process Work Area Characteristics data
wac_df = pd.read_csv(os.path.join(data_wac, 'wac_S000_JT00_2013.csv'), dtype=str)
wac_df['year'] = 2013

for year in range(2014, 2021):
    wac_year = pd.read_csv(os.path.join(data_wac, f'wac_S000_JT00_{year}.csv'), dtype=str)
    wac_year['year'] = year
    wac_df = pd.concat([wac_df, wac_year], ignore_index=True)

wac_df['paradise'] = 0
wac_df.loc[wac_df['w_tract'].isin(paradise_tracts), 'paradise'] = 1

wac_df.to_csv(os.path.join(data, "wac_2013_2020.csv"), index=False)

# Process Residence Area Characteristics data
rac_df = pd.read_csv(os.path.join(data_rac, 'rac_S000_JT00_2013.csv'), dtype=str)
rac_df['year'] = 2013

for year in range(2014, 2021):
    rac_year = pd.read_csv(os.path.join(data_rac, f'rac_S000_JT00_{year}.csv'), dtype=str)
    rac_year['year'] = year
    rac_df = pd.concat([rac_df, rac_year], ignore_index=True)

rac_df['paradise'] = 0
rac_df.loc[rac_df['h_tract'].isin(paradise_tracts), 'paradise'] = 1

rac_df.to_csv(os.path.join(data, "rac_2013_2020.csv"), index=False)
