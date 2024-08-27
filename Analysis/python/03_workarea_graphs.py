import os
import pandas as pd
import matplotlib.pyplot as plt

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
   

# Read in the work area characteristics data
wac_df = pd.read_csv(os.path.join(data, "wac_2013_2020.csv"))

# Create a frequency table of the paradise variable
freq_table = wac_df['paradise'].value_counts()
print(freq_table)

# Create a cross-tabulation of the year and paradise variables
table = pd.crosstab(wac_df['year'], wac_df['paradise'])
print(table)

# Group by paradise and year and sum all count variables
wac_grouped = wac_df.groupby(['paradise', 'year'], as_index=False).sum()

#create list of variables to loop over
jobvars =['C000','CA01','CA02','CA03','CE01','CE02','CE03','CNS01','CNS02','CNS03',
          'CNS04','CNS05','CNS06','CNS07','CNS08','CNS09','CNS10','CNS11','CNS12',
          'CNS13','CNS14','CNS15','CNS16','CNS17','CNS18','CNS19','CNS20','CR01',
          'CR02','CR03','CR04','CR05','CT01','CT02','CD01','CD02','CD03','CD04',
          'CS01','CS02']

# Keep only 2017, to use as base year for percentage change
wac_grouped_2017 = wac_grouped[wac_grouped['year'] == 2017]
wac_grouped_2017 = wac_grouped_2017.loc[:, ['paradise'] + jobvars]

# Create a dictionary to append _2017 to all of the variable names
rename_dict = {col: col + '_2017' for col in jobvars}
wac_grouped_2017 = wac_grouped_2017.rename(columns=rename_dict)

# Merge 2017 values to main dataframe
merged_df = pd.merge(wac_grouped, wac_grouped_2017, on='paradise')

#Calculate percent change from 2017
for var in jobvars:
    merged_df[var+'_pctchg']=(merged_df[var]-merged_df[var+'_2017'])/merged_df[var+'_2017']

    # Create line chart
    fig, ax = plt.subplots()
    # Filter data for paradise=1 and plot line
    paradise1 = merged_df[merged_df['paradise'] == 1]
    ax.plot(paradise1['year'], paradise1[var + '_pctchg'], marker='o', label='Paradise')
    # Filter data for paradise=0 and plot line
    paradise0 = merged_df[merged_df['paradise'] == 0]
    ax.plot(paradise0['year'], paradise0[var + '_pctchg'], marker='o', label='Rest of Butte County')
    ax.set_xlabel('Year')
    ax.set_ylabel('Percent Change')
    ax.set_title(f'Percent Change in Jobs (Base 2017) {var}')
    ax.legend()
    fig = plt.gcf()
    plt.tight_layout()
    plt.show()
    fig.savefig(os.path.join(graphs, var + '_workarea.png'))

