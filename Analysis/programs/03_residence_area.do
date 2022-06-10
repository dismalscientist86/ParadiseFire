/***************************************
*Filename: 03_residence_area.do
*Purpose: This program appends the three years of residence areas,
*	applies the "Paradise" dummy and other data cleaning tasks
*Created on: 6/10/2022
*Created by: Dani Sandler
*Modifications:
***************************************/
clear
capture log close

do 00_master_setup.do

log using $logs/03_residence_area$today.log, replace

use $data/rac_S000_JT00_2017.dta, clear
gen year=2017
append using $data/rac_S000_JT00_2018.dta
replace year=2018 if missing(year)
append using $data/rac_S000_JT00_2019.dta
replace year=2019 if missing(year)

*We will hopefully have a full list of geocodes soon, but here are 5 to work with for now
gen paradise=0
replace paradise=1 if h_geocode=="060070020001007"
replace paradise=1 if h_geocode=="060070019003001"
replace paradise=1 if h_geocode=="060070021001002"
replace paradise=1 if h_geocode=="060070022001006"
replace paradise=1 if h_geocode=="060070020002000"

graph bar (sum) c000 if paradise==1, over(year)

*To make line graphs, it is easiest to collapse down to one observation per location (Paradise/Not Paradise) per year
drop createdate
*All count variables start with c, so can use c* to include everything
collapse (sum) c*, by(paradise year)

*Two Y-axes are not ideal, but necessary to get Paradise and Not Paradise on the same graph, at least while using the 5 geocodes
graph twoway (connected c000 year if paradise==1, yaxis(1) ) (connected c000 year if paradise==0, yaxis(2)), xlabel(2017(1)2019) legend(label(1 "Paradise") label(2 "Rest of Butte County"))

*Percentage change to get them on same scale without playing with the axes
bysort paradise: egen c000_2017=max(c000*(year==2017))
gen c000_pctchg=(c000-c000_2017)/c000_2017

graph twoway (connected c000_pctchg year if paradise==1) (connected c000_pctchg year if paradise==0), xlabel(2017(1)2019) legend(label(1 "Paradise") label(2 "Rest of Butte County"))