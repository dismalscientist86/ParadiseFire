import os
import pandas as pd
import matplotlib.pyplot as plt

if os.getlogin() == "sandl305":
<<<<<<< HEAD:Analysis/python/02_residentialarea_graphs.py
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
   
=======
    programs = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\programs"
    data = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\data"
    output = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis"
    logs = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\programs\logs"
    graphs = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\graphs"
    data_od = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\data\lodes_od"
    data_rac = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\data\lodes_rac"
>>>>>>> a5ba01a38c641774b6108ffde781d45d0e186deb:Analysis/python/02_residenitalarea_graphs.py

# Read in data
rac = pd.read_csv(os.path.join(data, "rac_2013_2020.csv"))

# Print frequency table and crosstab
print(rac['paradise'].value_counts())
print(pd.crosstab(rac['year'], rac['paradise']))

# Group by paradise and year, sum all count variables
rac_grouped = rac.groupby(['paradise', 'year'], as_index=False).sum()

# List of variables to loop over
jobvars = [
    'C000', 'CA01', 'CA02', 'CA03', 'CE01', 'CE02', 'CE03', 'CNS01', 'CNS02', 'CNS03',
    'CNS04', 'CNS05', 'CNS06', 'CNS07', 'CNS08', 'CNS09', 'CNS10', 'CNS11', 'CNS12',
    'CNS13', 'CNS14', 'CNS15', 'CNS16', 'CNS17', 'CNS18', 'CNS19', 'CNS20', 'CR01',
    'CR02', 'CR03', 'CR04', 'CR05', 'CT01', 'CT02', 'CD01', 'CD02', 'CD03', 'CD04',
    'CS01', 'CS02'
]

# Keep only 2017, to use as base year for percentage change
rac_grouped_2017 = rac_grouped[rac_grouped['year'] == 2017].loc[:, ['paradise'] + jobvars]
rename_dict = {col: col + '_2017' for col in jobvars}
rac_grouped_2017 = rac_grouped_2017.rename(columns=rename_dict)

# Merge 2017 values to main dataframe
merged_df = pd.merge(rac_grouped, rac_grouped_2017, on='paradise')

# Calculate percent change from 2017 and create line charts
for var in jobvars:
    merged_df[var + '_pctchg'] = (merged_df[var] - merged_df[var + '_2017']) / merged_df[var + '_2017']

    fig, ax = plt.subplots()
    paradise1 = merged_df[merged_df['paradise'] == 1]
    paradise0 = merged_df[merged_df['paradise'] == 0]

    ax.plot(paradise1['year'], paradise1[var + '_pctchg'], marker='o', label='Paradise')
    ax.plot(paradise0['year'], paradise0[var + '_pctchg'], marker='o', label='Rest of Butte County')

    ax.set_xlabel('Year')
    ax.set_ylabel('Percent Change')
    ax.set_title(f'Percent Change in Jobs (Base 2017) {var}')
    ax.legend()

    plt.show()
    fig.savefig(os.path.join(graphs, f'{var}_residentialarea.png'))
