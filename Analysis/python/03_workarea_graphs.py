import pandas as pd
import matplotlib.pyplot as plt
from config import DATA_DIR, GRAPHS_DIR

# Read in data
wac = pd.read_csv(DATA_DIR / "wac_2013_2020.csv")

# Print frequency table and crosstab
print(wac['paradise'].value_counts())
print(pd.crosstab(wac['year'], wac['paradise']))

# Group by paradise and year, sum all count variables
wac_grouped = wac.groupby(['paradise', 'year'], as_index=False).sum()

# List of variables to loop over
jobvars = [
    'C000', 'CA01', 'CA02', 'CA03', 'CE01', 'CE02', 'CE03', 'CNS01', 'CNS02', 'CNS03',
    'CNS04', 'CNS05', 'CNS06', 'CNS07', 'CNS08', 'CNS09', 'CNS10', 'CNS11', 'CNS12',
    'CNS13', 'CNS14', 'CNS15', 'CNS16', 'CNS17', 'CNS18', 'CNS19', 'CNS20', 'CR01',
    'CR02', 'CR03', 'CR04', 'CR05', 'CT01', 'CT02', 'CD01', 'CD02', 'CD03', 'CD04',
    'CS01', 'CS02'
]

# Keep only 2017, to use as base year for percentage change
wac_grouped_2017 = wac_grouped[wac_grouped['year'] == 2017].loc[:, ['paradise'] + jobvars]
rename_dict = {col: col + '_2017' for col in jobvars}
wac_grouped_2017 = wac_grouped_2017.rename(columns=rename_dict)

# Merge 2017 values to main dataframe
merged_df = pd.merge(wac_grouped, wac_grouped_2017, on='paradise')

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
    plt.tight_layout()

    plt.show()
    fig.savefig(GRAPHS_DIR / f'{var}_workarea.png')
