import os
import requests
import gzip
import shutil
import pandas as pd

if os.getlogin() == "sandl305":
    programs = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\programs"
    data = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\data"
    output = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis"
    logs = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\programs\logs"
    graphs = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\graphs"
    data_od = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\data\lodes_od"
    data_rac = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\data\lodes_rac"
    data_wac = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\data\lodes_wac" 
    
#Bring in Origin-Destination Main dataset, for All Jobs (JT00)
#Note - I do not understand why having the range go through 2021 means files are downloaded through 2020, but if the range went to 2020 it only downloaded up to 2019
for i in range(2013,2021):	
    url = f"https://lehd.ces.census.gov/data/lodes/LODES8/ca/od/ca_od_main_JT00_{i}.csv.gz"
    file_path = os.path.join(data_od, f"ca_od_main_JT00_{i}.csv.gz")

    response = requests.get(url, stream=True)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(response.raw, f)

    with gzip.open(file_path, "rb") as f_in:
        with open(os.path.splitext(file_path)[0], "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    # Read in CSV file
    df = pd.read_csv(file_path, dtype=str)

    # Create county FIPS from first five digits of geocode
    df["w_county"] = df["w_geocode"].str[:5]
    df["h_county"] = df["h_geocode"].str[:5]

    # Keep only Butte County (FIPS=06007)
    df = df[(df["w_county"] == "06007") | (df["h_county"] == "06007")]
    
    # Save resulting data as CSV file
    df.to_csv(os.path.join(data_od, f"od_main_JT00_{i}.csv"), index=False)
    
#Bring in Residence Area Characteristics Main dataset, for All Jobs (JT00)
for i in range(2013,2021):	
    url = f"https://lehd.ces.census.gov/data/lodes/LODES8/ca/rac/ca_rac_S000_JT00_{i}.csv.gz"
    file_path = os.path.join(data_rac, f"ca_rac_S000_JT00_{i}.csv.gz")

    response = requests.get(url, stream=True)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(response.raw, f)

    with gzip.open(file_path, "rb") as f_in:
        with open(os.path.splitext(file_path)[0], "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    # Read in CSV file
    df = pd.read_csv(file_path, dtype=str)

    # Create county FIPS from first five digits of geocode
    df["h_county"] = df["h_geocode"].str[:5]

    # Keep only Butte County (FIPS=06007)
    df = df[(df["h_county"] == "06007")]
    
    # Save resulting data as CSV file
    df.to_csv(os.path.join(data_rac, f"rac_S000_JT00_{i}.csv"), index=False)
    
#Bring in Work Area Characteristics Main dataset, for All Jobs (JT00)
for i in range(2013,2021):	
    url = f"https://lehd.ces.census.gov/data/lodes/LODES8/ca/wac/ca_wac_S000_JT00_{i}.csv.gz"
    file_path = os.path.join(data_wac, f"ca_wac_S000_JT00_{i}.csv.gz")

    response = requests.get(url, stream=True)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(response.raw, f)

    with gzip.open(file_path, "rb") as f_in:
        with open(os.path.splitext(file_path)[0], "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    # Read in CSV file
    df = pd.read_csv(file_path, dtype=str)

    # Create county FIPS from first five digits of geocode
    df["w_county"] = df["w_geocode"].str[:5]

    # Keep only Butte County (FIPS=06007)
    df = df[(df["w_county"] == "06007")]
    
    # Save resulting data as CSV file
    df.to_csv(os.path.join(data_wac, f"wac_S000_JT00_{i}.csv"), index=False)
    
#Append data from years 2013-2020 and flag Paradise geocodes
wac_files=[os.path.join(data_wac,f"wac_S000_JT00_{i}.csv") for i in range(2013,2020)]

#Read in first year and create year variable
wac_df=pd.read_csv(wac_files[0])
wac_df["year"]=2013

