***************************************
*Filename: 03_residence_area.do
*Purpose: This program appends the three years of residence areas,
*	applies the "Paradise" dummy and other data cleaning tasks
*Created on: 6/10/2022
*Modifications:
*	7/1/22 - Added data from 2013 to 2016, added percent change variables
***************************************
clear
capture log close

do 00_master_setup.do

log using $logs/03_residence_area$today.log, replace

use $data/rac_S000_JT00_2013.dta, clear
gen year=2013
append using $data/rac_S000_JT00_2014.dta
replace year=2014 if missing(year)
append using $data/rac_S000_JT00_2015.dta
replace year=2015 if missing(year)
append using $data/rac_S000_JT00_2016.dta
replace year=2016 if missing(year)
append using $data/rac_S000_JT00_2017.dta
replace year=2017 if missing(year)
append using $data/rac_S000_JT00_2018.dta
replace year=2018 if missing(year)
append using $data/rac_S000_JT00_2019.dta
replace year=2019 if missing(year)


*I think Paradise Census Tracts are tracts 18,19, 20, 21 within Butte County
gen h_tract=substr(h_geocode,1,9)
gen paradise=0
replace paradise=1 if h_tract=="060070018"
replace paradise=1 if h_tract=="060070019"
replace paradise=1 if h_tract=="060070020"
replace paradise=1 if h_tract=="060070021"

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


** Create Percent change variables for each subgroup, to get them on same scale without playing with the axes

*age 
forvalues i = 1 / 3 {
	bysort paradise: egen ca0`i'_2013=max(ca0`i'*(year==2013))
 gen ca0`i'_pctchg=100*(ca0`i'-ca0`i'_2013)/ca0`i'_2013
}

*income
forvalues i = 1 / 3 {
 	bysort paradise: egen ce0`i'_2013=max(ce0`i'*(year==2013))
 gen ce0`i'_pctchg=100*(ce0`i'-ce0`i'_2013)/ce0`i'_2013
}

*industry pt 1
forvalues i = 1 / 9 {
	bysort paradise: egen cns0`i'_2013=max(cns0`i'*(year==2013))
 gen cns0`i'_pctchg=100*(cns0`i'-cns0`i'_2013)/cns0`i'_2013
}
 
 

*industry pt 2
forvalues i = 10 / 20 {
	bysort paradise: egen cns`i'_2013=max(cns`i'*(year==2013))
 gen cns`i'_pctchg=100*(cns`i'-cns`i'_2013)/cns`i'_2013
}

*race
forvalues i = 1 / 5 {
	bysort paradise: egen cr0`i'_2013=max(cr0`i'*(year==2013))
 gen cr0`i'_pctchg=100*(cr0`i'-cr0`i'_2013)/cr0`i'_2013
}
	bysort paradise: egen cr07_2013=max(cr07*(year==2013))
 gen cr07_pctchg=100*(cr07 - cr07_2013)/cr07_2013


*ethnicity
forvalues i = 1 / 2 {
	bysort paradise: egen ct0`i'_2013=max(ct0`i'*(year==2013))
 gen ct0`i'_pctchg=100*(ct0`i'-ct0`i'_2013)/ct0`i'_2013
}

*educational attainment 
forvalues i = 1 / 4 {
	bysort paradise: egen cd0`i'_2013=max(cd0`i'*(year==2013))
 gen cd0`i'_pctchg=100*(cd0`i'-cd0`i'_2013)/cd0`i'_2013
}

*sex
forvalues i = 1 / 2 {
	bysort paradise: egen cs0`i'_2013=max(cs0`i'*(year==2013))
 gen cs0`i'_pctchg=100*(cs0`i'-cs0`i'_2013)/cs0`i'_2013
}
