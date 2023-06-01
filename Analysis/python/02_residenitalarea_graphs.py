import os
import pandas as pd
import matplotlib.pyplot as plt

if os.getlogin() == "sandl305":
    programs = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\programs"
    data = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\data"
    output = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis"
    logs = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\programs\logs"
    graphs = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\graphs"
    data_od = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\data\lodes_od"
    data_rac = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\data\lodes_rac"
    data_rac = r"C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\data\lodes_rac" 
   

# read in data
rac = pd.read_csv(os.path.join(data, "rac_2013_2020.csv"))

freq_table = rac['paradise'].value_counts()
print(freq_table)

table=pd.crosstab(rac['year'],rac['paradise'])
print(table)

# group by paradise and year and sum all count variables
rac_grouped = rac.groupby(['paradise', 'year'], as_index=False).sum()

#create list of variables to loop over
jobvars =['C000','CA01','CA02','CA03','CE01','CE02','CE03','CNS01','CNS02','CNS03',
          'CNS04','CNS05','CNS06','CNS07','CNS08','CNS09','CNS10','CNS11','CNS12',
          'CNS13','CNS14','CNS15','CNS16','CNS17','CNS18','CNS19','CNS20','CR01',
          'CR02','CR03','CR04','CR05','CT01','CT02','CD01','CD02','CD03','CD04',
          'CS01','CS02']
#Keep only 2017, to use as base year for percentage change
rac_grouped_2017=rac_grouped[rac_grouped['year']==2017]
rac_grouped_2017=rac_grouped_2017.loc[:,['paradise']+ jobvars]
#Create a dictorary to append _2017 to all of the variables names
rename_dict={col:col + '_2017' for col in jobvars}
rac_grouped_2017=rac_grouped_2017.rename(columns=rename_dict)

#Merge 2017 values to main dataframe
merged_df=pd.merge(rac_grouped,rac_grouped_2017, on='paradise')

#Calculate percent change from 2017
for var in jobvars:
    merged_df[var+'_pctchg']=(merged_df[var]-merged_df[var+'_2017'])/merged_df[var+'_2017']

    #Create line chart
    fig, ax=plt.subplots()
    #Filter data for paradise=1 and plot line
    paradise1=merged_df[merged_df['paradise']==1]
    ax.plot(paradise1['year'],paradise1[var+'_pctchg'],marker='o',label='Paradise')
    #Filter data for paradise=0 and plot line
    paradise0=merged_df[merged_df['paradise']==0]
    ax.plot(paradise0['year'],paradise0[var+'_pctchg'],marker='o',label='Rest of Butte County')
    ax.set_xlabel('Year')
    ax.set_ylabel('Percent Change')
    ax.set_title('Percent Change in Jobs (Base 2017) '+var)
    ax.legend()
    fig=plt.gcf()
    plt.show()
    fig.savefig(os.path.join(graphs,var+'_residentialarea.png'))

