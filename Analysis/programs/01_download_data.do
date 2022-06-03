/****************************
*Program Name: 01_download_data.do
*Purpose: This program downloads the LODES data from the website 
*and puts it into subfolders within the $data directory. These still
*need to be unzipped after downloading. I couldn't figure out how to 
*do that from within Stata (running on Windows)
*Created by: Dani Sandler
*Created on: 5/27/2022
*Modifications: 6/3/22 - DHS - Add dated log file
******************************/
clear
capture log close

do 00_master_setup.do

log using $logs/01_download_data$today.log, replace

*Just download 2017, 2018, and 2019 data for now. Can expand loop if want more years.
forvalues yr=2017/2019{
	forvalues i=0/1{
		quietly copy https://lehd.ces.census.gov/data/lodes/LODES7/ca/od/ca_od_main_JT0`i'_`yr'.csv.gz $data/lodes_od/ca_od_main_JT0`i'_`yr'.csv.gz, replace
		quietly copy https://lehd.ces.census.gov/data/lodes/LODES7/ca/od/ca_od_aux_JT0`i'_`yr'.csv.gz $data/lodes_od/ca_od_aux_JT0`i'_`yr'.csv.gz, replace
		
		quietly copy https://lehd.ces.census.gov/data/lodes/LODES7/ca/rac/ca_rac_S000_JT0`i'_`yr'.csv.gz $data/lodes_rac/ca_rac_S000_JT0`i'_`yr'.csv.gz, replace
		quietly copy https://lehd.ces.census.gov/data/lodes/LODES7/ca/rac/ca_rac_SA01_JT0`i'_`yr'.csv.gz $data/lodes_rac/ca_rac_SA01_JT0`i'_`yr'.csv.gz, replace
		quietly copy https://lehd.ces.census.gov/data/lodes/LODES7/ca/rac/ca_rac_SA02_JT0`i'_`yr'.csv.gz $data/lodes_rac/ca_rac_SA02_JT0`i'_`yr'.csv.gz, replace
		quietly copy https://lehd.ces.census.gov/data/lodes/LODES7/ca/rac/ca_rac_SA03_JT0`i'_`yr'.csv.gz $data/lodes_rac/ca_rac_SA03_JT0`i'_`yr'.csv.gz, replace
		quietly copy https://lehd.ces.census.gov/data/lodes/LODES7/ca/rac/ca_rac_SE01_JT0`i'_`yr'.csv.gz $data/lodes_rac/ca_rac_SE01_JT0`i'_`yr'.csv.gz, replace
		quietly copy https://lehd.ces.census.gov/data/lodes/LODES7/ca/rac/ca_rac_SE02_JT0`i'_`yr'.csv.gz $data/lodes_rac/ca_rac_SE02_JT0`i'_`yr'.csv.gz, replace
		quietly copy https://lehd.ces.census.gov/data/lodes/LODES7/ca/rac/ca_rac_SE03_JT0`i'_`yr'.csv.gz $data/lodes_rac/ca_rac_SE03_JT0`i'_`yr'.csv.gz, replace
		quietly copy https://lehd.ces.census.gov/data/lodes/LODES7/ca/rac/ca_rac_SI01_JT0`i'_`yr'.csv.gz $data/lodes_rac/ca_rac_SI01_JT0`i'_`yr'.csv.gz, replace
		quietly copy https://lehd.ces.census.gov/data/lodes/LODES7/ca/rac/ca_rac_SI02_JT0`i'_`yr'.csv.gz $data/lodes_rac/ca_rac_SI02_JT0`i'_`yr'.csv.gz, replace
		quietly copy https://lehd.ces.census.gov/data/lodes/LODES7/ca/rac/ca_rac_SI03_JT0`i'_`yr'.csv.gz $data/lodes_rac/ca_rac_SI03_JT0`i'_`yr'.csv.gz, replace
		
		quietly copy https://lehd.ces.census.gov/data/lodes/LODES7/ca/wac/ca_wac_S000_JT0`i'_`yr'.csv.gz $data/lodes_wac/ca_wac_S000_JT0`i'_`yr'.csv.gz, replace
		quietly copy https://lehd.ces.census.gov/data/lodes/LODES7/ca/wac/ca_wac_SA01_JT0`i'_`yr'.csv.gz $data/lodes_wac/ca_wac_SA01_JT0`i'_`yr'.csv.gz, replace
		quietly copy https://lehd.ces.census.gov/data/lodes/LODES7/ca/wac/ca_wac_SA02_JT0`i'_`yr'.csv.gz $data/lodes_wac/ca_wac_SA02_JT0`i'_`yr'.csv.gz, replace
		quietly copy https://lehd.ces.census.gov/data/lodes/LODES7/ca/wac/ca_wac_SA03_JT0`i'_`yr'.csv.gz $data/lodes_wac/ca_wac_SA03_JT0`i'_`yr'.csv.gz, replace
		quietly copy https://lehd.ces.census.gov/data/lodes/LODES7/ca/wac/ca_wac_SE01_JT0`i'_`yr'.csv.gz $data/lodes_wac/ca_wac_SE01_JT0`i'_`yr'.csv.gz, replace
		quietly copy https://lehd.ces.census.gov/data/lodes/LODES7/ca/wac/ca_wac_SE02_JT0`i'_`yr'.csv.gz $data/lodes_wac/ca_wac_SE02_JT0`i'_`yr'.csv.gz, replace
		quietly copy https://lehd.ces.census.gov/data/lodes/LODES7/ca/wac/ca_wac_SE03_JT0`i'_`yr'.csv.gz $data/lodes_wac/ca_wac_SE03_JT0`i'_`yr'.csv.gz, replace
		quietly copy https://lehd.ces.census.gov/data/lodes/LODES7/ca/wac/ca_wac_SI01_JT0`i'_`yr'.csv.gz $data/lodes_wac/ca_wac_SI01_JT0`i'_`yr'.csv.gz, replace
		quietly copy https://lehd.ces.census.gov/data/lodes/LODES7/ca/wac/ca_wac_SI02_JT0`i'_`yr'.csv.gz $data/lodes_wac/ca_wac_SI02_JT0`i'_`yr'.csv.gz, replace
		quietly copy https://lehd.ces.census.gov/data/lodes/LODES7/ca/wac/ca_wac_SI03_JT0`i'_`yr'.csv.gz $data/lodes_wac/ca_wac_SI03_JT0`i'_`yr'.csv.gz, replace
		
	}
}
	


*California Geography Crosswalk	
quietly copy https://lehd.ces.census.gov/data/lodes/LODES7/ca/ca_xwalk.csv.gz $data/ca_xwalk.csv.gz, replace

