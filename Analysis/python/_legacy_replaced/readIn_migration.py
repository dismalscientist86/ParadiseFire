# -*- coding: utf-8 -*-
"""
Created on Wed Jan 31 16:42:22 2024

@author: sandl305
"""

import os
import requests
import pandas as pd
import chardet
import logging



if os.getlogin() == "sandl305":
    # Define the base directory for the project
    base_dir = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis"

# Define the subdirectories for programs, data, output, logs, and graphs
programs = os.path.join(base_dir, "programs")
data = os.path.join(base_dir, "data")
output = base_dir
logs = os.path.join(programs, "logs")
graphs = os.path.join(base_dir, "graphs")
data_od = os.path.join(data, "lodes_od")
data_rac = os.path.join(data, "lodes_rac")
data_wac = os.path.join(data, "lodes_wac")
data_mig = os.path.join(data, "migration") 

# Set up logging
logging.basicConfig(filename=os.path.join(programs, "logs", "migration_analysis.log"), level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.info("Starting migration analysis")


# Bring in 2016-2020 County-to-County migration data
url = "https://www2.census.gov/programs-surveys/demo/tables/geographic-mobility/2020/county-to-county-migration-2016-2020/county-to-county-migration-flows/Net_Gross_US.txt"
file_path = os.path.join(data_mig, "Net_Gross_US.txt")

# Download the file from the URL
try:
    logging.info(f"Downloading the file from {url}")
    response = requests.get(url, stream=True)
    with open(file_path, "wb") as f:
        f.write(response.content)
    logging.info(f"File downloaded successfully and saved as {file_path}")
except Exception as e:
    logging.error(f"Failed to download the file from {url}: {e}")
    raise e

# Detect the encoding of the file
try:
    logging.info(f"Detecting the encoding of the file {file_path}")
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read()) # or readline if the file is large
    logging.info(f"Encoding detected as {result['encoding']}")
except Exception as e:
    logging.error(f"Failed to detect the encoding of the file {file_path}: {e}")
    raise e

# Read the fixed width file and return the data frame
try:
    logging.info(f"Reading the fixed width file {file_path} and returning the data frame")
    df = pd.read_fwf(file_path, header=None, colspecs=[(1,11), (13,41), (43,77), (79,107), (109,149), (151,158), (160,166), (168,175), (177,183), (185,193), (195,202), (204,211), (213,217)],
                    names=["FIPS","State_name_A","County_name_A","State_name_B","County_name_B","Flow_B2A","Flow_B2A_MOE",
                            "Flow_A2B","Flow_A2B_MOE","Net_B2A","Net_B2A_MOE","Gross_A2B","Gross_A2B_MOE"],
                    encoding=result['encoding'])
    logging.info(f"Data frame created successfully with shape {df.shape}")
except Exception as e:
    logging.error(f"Failed to read the fixed width file {file_path} and return the data frame: {e}")
    raise e

# Filter the data frame for Butte County, California
try:
    logging.info("Filtering the data frame for Butte County, California")
    butte_df = df.query("County_name_A == 'Butte County' and State_name_A == 'California'")
    logging.info(f"Data frame filtered successfully with shape {butte_df.shape}")
except Exception as e:
    logging.error(f"Failed to filter the data frame for Butte County, California: {e}")
    raise e

# Get the summary of the data frame
logging.info("Getting the summary of the data frame")
print(butte_df.info())

# Get the basic statistics of the numeric columns
logging.info("Getting the basic statistics of the numeric columns")
print(butte_df.describe())

# Get the first 5 rows of the data frame
logging.info("Getting the first 5 rows of the data frame")
print(butte_df.head())

# Get the last 5 rows of the data frame
logging.info("Getting the last 5 rows of the data frame")
print(butte_df.tail())

# Get the total net migration for Butte County
logging.info("Getting the total net migration for Butte County")
print(butte_df["Net_B2A"].sum())

# Get the average net migration for Butte County
logging.info("Getting the average net migration for Butte County")
print(butte_df["Net_B2A"].mean())

# Get the maximum net migration for Butte County
logging.info("Getting the maximum net migration for Butte County")
print(butte_df["Net_B2A"].max())

# Get the minimum net migration for Butte County
logging.info("Getting the minimum net migration for Butte County")
print(butte_df["Net_B2A"].min())

# Get the index of the row with the maximum net migration
logging.info("Getting the index of the row with the maximum net migration")
print(butte_df["Net_B2A"].idxmax())

# Get the index of the row with the minimum net migration
logging.info("Getting the index of the row with the minimum net migration")
print(butte_df["Net_B2A"].idxmin())

# Get the row with the maximum net migration
logging.info("Getting the row with the maximum net migration")
print(butte_df.loc[butte_df["Net_B2A"].idxmax()])

# Get the row with the minimum net migration
logging.info("Getting the row with the minimum net migration")
print(butte_df.loc[butte_df["Net_B2A"].idxmin()])

# Import matplotlib and seaborn for plotting
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_theme()

# Plot a bar chart of the net migration by county of prior residence
logging.info("Plotting a bar chart of the gross migration by county")
plt.figure(figsize=(10, 6))
sns.barplot(data=butte_df, x="Gross_A2B", y="County_name_B", color="blue")
plt.title("Gross Migration by Current Residence County for Butte County, California")
plt.xlabel("Gross Migration")
plt.ylabel("County of Prior Residence")
plt.show()

# Plot a bar chart of the net migration by current residence county
logging.info("Plotting a bar chart of the net migration by current residence county")
plt.figure(figsize=(10, 6))
sns.barplot(data=butte_df, x="Net_B2A", y="County_name_B", color="green")
plt.title("Net Migration by Current Residence County for Butte County, California")
plt.xlabel("Net Migration")
plt.ylabel("Current Residence County")
plt.show()

# Plot a scatter plot of the gross migration vs net migration
logging.info("Plotting a scatter plot of flows from Butte and flows to Butte")
plt.figure(figsize=(10, 6))
sns.scatterplot(data=butte_df, x="Flow_A2B", y="Flow_B2A", hue="Net_B2A")
plt.title("Flows to and from for Butte County, California")
plt.xlabel("Flows from Butte")
plt.ylabel("Flows to Butte")
plt.legend(title="Net_B2A")
plt.show()

# Sort by NetB2A in descending order
butte_df = butte_df.sort_values(by="Net_B2A", ascending=False)

# Set the display.max_columns option to None
pd.set_option('display.max_columns', None)


# Show the top 5 observations
print(butte_df.head())

# Print the last 5 rows of the data frame without NaN values
print(df.dropna().pipe(print).tail())

logging.info("Ending migration analysis")
