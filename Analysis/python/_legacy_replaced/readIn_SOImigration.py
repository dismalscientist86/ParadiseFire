# -*- coding: utf-8 -*-
"""
Created on Fri Feb  2 13:47:27 2024

@author: sandl305
"""

# Import pandas library
import pandas as pd
import datetime as dt
# Import matplotlib library
import matplotlib.pyplot as plt

# Define a dictionary of the URLs of the CSV files for each year
urls = {"2014-2015": "https://www.irs.gov/pub/irs-soi/countyoutflow1415.csv",
        "2015-2016": "https://www.irs.gov/pub/irs-soi/countyoutflow1516.csv",
        "2016-2017": "https://www.irs.gov/pub/irs-soi/countyoutflow1617.csv",
        "2017-2018": "https://www.irs.gov/pub/irs-soi/countyoutflow1718.csv",
        "2018-2019": "https://www.irs.gov/pub/irs-soi/countyoutflow1819.csv",
        "2019-2020": "https://www.irs.gov/pub/irs-soi/countyoutflow1920.csv",
        "2020-2021": "https://www.irs.gov/pub/irs-soi/countyoutflow2021.csv"}

# Initialize an empty dictionary to store the totals for each year
totals = {}

# Loop over the dictionary keys and values
for year, url in urls.items():
    # Read the CSV file from the URL and store it as a pandas data frame
    df = pd.read_csv(url, dtype=str)

    # Convert the columns n1 and agi to numeric variables
    df["n1"] = pd.to_numeric(df["n1"])
    df["agi"] = pd.to_numeric(df["agi"])

    # Filter the data by county code and state code
    # According to the SOI documentation, the county code for Butte County is 007 and the state code for California is 06
    butte_df = df[(df["y1_statefips"] == "06") & (df["y1_countyfips"] == "007")]

    # Calculate the total number of exemptions and the total adjusted gross income that left Butte County in the year
    # The column n1 is the number of exemptions, the column agi is the adjusted gross income
    total_exemptions = butte_df["n1"].sum()
    total_income = butte_df["agi"].sum()

    # Store the totals in the dictionary with the year as the key
    totals[year] = (total_exemptions, total_income)

# Print the dictionary
print(totals)

# Concatenate the total exemptions and income for each year into a data frame
totals_df = pd.DataFrame(totals).T

# Rename the columns
totals_df.columns = ["Exemptions", "Income"]

# Print the data frame
print(totals_df)

# Convert the strings to datetime objects
totals_df.index = [dt.datetime.strptime(year.split("-")[1], "%Y") for year in totals_df.index]

# Plot the exemptions and income on two different y-axes
totals_df.plot(kind="line", xticks=totals_df.index, title="Exemptions and Income that left Butte County", secondary_y=["Income"])

# Format the xticks as year-year
plt.gca().xaxis.set_major_formatter(md.DateFormatter("%Y-%Z"))

# Show the plot
plt.show()
