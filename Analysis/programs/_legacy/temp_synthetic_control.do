forvalues i=2017/2019{
	insheet using $data/lodes_rac/ca_rac_S000_JT00_`i'.csv, double clear

	*Convert geocodes to string variables
	tostring h_geocode, replace format(%14.0f)
	*Add a zero to be consistent with standard FIPS formatting
	replace h_geocode="0"+h_geocode

	*Create county FIPS from first five digits of geocode
	gen h_county=substr(h_geocode,1,5)
    
	tempfile rac_`i'
	save `rac_`i'', replace
}

use `rac_2017'
gen year=2017
append using `rac_2018'
replace year=2018 if missing(year)
append using `rac_2019'
replace year=2019 if missing(year)

*I think Paradise Census Tracts are tracts 18,19, 20, 21 within Butte County
gen h_tract=substr(h_geocode,1,9)

gen paradise=0

replace paradise=1 if h_tract=="060070018"

replace paradise=1 if h_tract=="060070019"

replace paradise=1 if h_tract=="060070020"

replace paradise=1 if h_tract=="060070021"

replace h_tract="paradise" if paradise==1

*Aggregate to tracts
drop createdate
*All count variables start with c, so can use c* to include everything
collapse (sum) c*, by(h_tract year)


*control varibales 
gen age_pwork = ca02/c000

gen ed_hsplus = (cd02+cd03)/c000

gen ed_college = cd04/c000

gen p_female = cs02/c000

egen geoid=group(h_tract)

xtset geoid year

summ geoid if h_tract=="paradise"
local paradise=`r(max)'
display `paradise'

synth c000 age_pwork(2017) ed_hsplus(2017) ed_college(2017) p_female(2017), trunit(`paradise') trperiod(2018)