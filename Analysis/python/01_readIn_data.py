import os
import requests
import gzip
import shutil

if os.getlogin() == "sandl305":
    programs = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\programs"
    data = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\data"
    output = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\"
    logs = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\programs\logs"
    graphs = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\graphs"
	
url = "https://lehd.ces.census.gov/data/lodes/LODES8/ca/od/ca_od_main_JT00_2020.csv.gz"
file_path = os.path.join(data, "ca_od_main_JT00_2020.csv.gz")

response = requests.get(url, stream=True)
with open(file_path, "wb") as f:
    shutil.copyfileobj(response.raw, f)

with gzip.open(file_path, "rb") as f_in:
    with open(os.path.splitext(file_path)[0], "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)

#Bring in Origin-Destination Main dataset, for All Jobs (JT00)		
# Read in CSV file
df = pd.read_csv(file_path)

# Convert geocodes to string variables
df["w_geocode"] = df["w_geocode"].astype(str).str.pad(width=15, fillchar="0")
df["h_geocode"] = df["h_geocode"].astype(str).str.pad(width=15, fillchar="0")

# Add a leading zero to geocodes
df["w_geocode"] = "0" + df["w_geocode"]
df["h_geocode"] = "0" + df["h_geocode"]

# Create county FIPS from first five digits of geocode
df["w_county"] = df["w_geocode"].str[:5]
df["h_county"] = df["h_geocode"].str[:5]

# Keep only Butte County (FIPS=06007)
df = df.loc[(df["w_county"] == "06007") | (df["h_county"] == "06007")]

# Save resulting data as CSV file
df.to_csv(os.path.join(data_dir, "od_main_JT00_2020.csv"), index=False)