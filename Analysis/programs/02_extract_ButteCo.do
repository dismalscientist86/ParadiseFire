/***************************************
*Filename: 02_extract_butteCou.do
*Purpose: To bring in the .csv data, keep only 
Butte county, and save as Stata datasets
*Created on: 6/3/2022
*Modifications:
*	6/10/22 - Change to loop for 2017-2019
					Add extract of RAC and WAC datasets
***************************************/
clear
capture log close

do 00_master_setup.do

log using $logs/02_extract_ButteCo$today.log, replace

*Bring in Origin-Destination Main dataset, for All Jobs (JT00)
*Make sure to bring in as double so it doesn't round the geocode variables
forvalues i=2013/2019{
	insheet using $data/lodes_od/ca_od_main_JT00_`i'.csv, double clear

	*Convert geocodes to string variables
	tostring w_geocode, replace format(%14.0f)
	tostring h_geocode, replace format(%14.0f)
	*Add a zero to be consistent with standard FIPS formatting
	replace w_geocode="0"+w_geocode
	replace h_geocode="0"+h_geocode

	*Create county FIPS from first five digits of geocode
	gen w_county=substr(w_geocode,1,5)
	gen h_county=substr(h_geocode,1,5)

	*Keep only Butte County (FIPS=06007)
	keep if w_county=="06007" | h_county=="06007"

	save $data/od_main_JT00_`i'.dta, replace
}

*Bring in Residential Area Characteristics Main dataset, for All Jobs (JT00)
*Make sure to bring in as double so it doesn't round the geocode variables
forvalues i=2013/2019{
	insheet using $data/lodes_rac/ca_rac_S000_JT00_`i'.csv, double clear

	*Convert geocodes to string variables
	tostring h_geocode, replace format(%14.0f)
	*Add a zero to be consistent with standard FIPS formatting
	replace h_geocode="0"+h_geocode

	*Create county FIPS from first five digits of geocode
	gen h_county=substr(h_geocode,1,5)

	*Keep only Butte County (FIPS=06007)
	keep if h_county=="06007"

	save $data/rac_S000_JT00_`i'.dta, replace
}


*Bring in Work Area Characteristics Main dataset, for All Jobs (JT00)
*Make sure to bring in as double so it doesn't round the geocode variables
forvalues i=2013/2019{
	insheet using $data/lodes_wac/ca_wac_S000_JT00_`i'.csv, double clear

	*Convert geocodes to string variables
	tostring w_geocode, replace format(%14.0f)
	*Add a zero to be consistent with standard FIPS formatting
	replace w_geocode="0"+w_geocode
	
	*Create county FIPS from first five digits of geocode
	gen w_county=substr(w_geocode,1,5)
	
	*Keep only Butte County (FIPS=06007)
	keep if w_county=="06007" 

	save $data/wac_S000_JT00_`i'.dta, replace
}