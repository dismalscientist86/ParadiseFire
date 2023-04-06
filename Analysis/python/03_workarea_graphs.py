# read in data
wac = pd.read_csv(os.path.join(data, "wac_2013_2020.csv"))

# group by paradise and year and sum all count variables
wac_grouped = wac.groupby(['paradise', 'year'], as_index=False).sum()

# calculate percentage change from 2017 for c000 and add to new column
wac_grouped['c000_2017'] = wac_grouped.groupby('paradise')['c000'].transform(lambda x: x[x['year']==2017].iloc[0])
wac_grouped['c000_pctchg'] = (wac_grouped['c000'] - wac_grouped['c000_2017']) / wac_grouped['c000_2017']

# plot line graph with two y-axes
fig, ax1 = plt.subplots()

# plot line graph for paradise tracts on first y-axis
paradise_data = wac_grouped[wac_grouped['paradise']==1]
ax1.plot(paradise_data['year'], paradise_data['c000'], label='Paradise', color='blue')
ax1.set_xlabel('Year')
ax1.set_ylabel('Total Jobs (Paradise)', color='blue')

# plot line graph for non-paradise tracts on second y-axis
non_paradise_data = wac_grouped[wac_grouped['paradise']==0]
ax2 = ax1.twinx()
ax2.plot(non_paradise_data['year'], non_paradise_data['c000'], label='Rest of Butte County', color='orange')
ax2.set_ylabel('Total Jobs (Rest of Butte County)', color='orange')

# add legend and title
fig.legend()
fig.suptitle('Total Jobs by Year and Location')

# plot line graph of percentage change
fig, ax = plt.subplots()
ax.plot(paradise_data['year'], paradise_data['c000_pctchg'], label='Paradise', color='blue')
ax.plot(non_paradise_data['year'], non_paradise_data['c000_pctchg'], label='Rest of Butte County', color='orange')
ax.set_xlabel('Year')
ax.set_ylabel('Percentage Change from 2017')
ax.legend()
fig.suptitle('Percentage Change in Total Jobs by Year and Location')