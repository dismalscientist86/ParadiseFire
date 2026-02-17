/***************************************
*Filename: 05_Bar_graphs_subgroups.do
*Purpose: This program creates bar graphs with number of Paradise employees by subcategory
	for years 2017, 2018, and 2019
*Created on: 6/24/2022
*Modifications:
*	7/1/22 - Added header, added 00_master_setup.do at start,
*	used macros to save paths, removed .gph save,
*	added graphs for both rac & wac
***************************************/
do 00_master_setup.do

capture log close
log using $logs/05_Bar_graphs_subgroups$today.log, replace

*Bring in Residence area data
use $data/rac_S000_JT00_2017.dta, clear
gen year=2017
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


** Total jobs by subgroup 


*Change in jobs per age group 
graph bar (sum) ca01 ca02 ca03 if paradise == 1, over (year) title("Total Jobs per age group") legend (label(1 "29 and younger") label(2 "30 to 54") label (3 "55 and older")) 
graph export ${graphs}/total_jobs_per_age_rac.jpg, replace

*Change in jobs per earnings

graph bar (sum) ce01 ce02 ce03 if paradise == 1, over (year) title("Total Jobs per Monthly Earnings") legend (label(1 "earnings $1250 or less") label(2 "earnings $1251 - $3333") label (3 "earnings greater than $3333") size(small)) 
graph export ${graphs}/total_jobs_earnings_rac.jpg, replace

*Change in jobs per idustry group (ALL)

*graph bar (sum) cns01 cns02 cns03 cns04 cns05 cns06 cns07 cns08 cns09 cns10 cns11 cns12 cns13 cns14 cns15 cns16 cns17 cns18 cns19 cns20 if paradise == 1, over (year) title("Total Jobs per Industry")legend(label(1 "Agriculture, Forestry, Fishing and Hunting") label(2 "Mining, Quarrying, and Oil and Gas Extraction") label(3 "Utilities") label(4 "Construction") label(5 "Manufacturing") label(6 "Wholesale Trade") label(7 "Retail Trade") label(8 "Transportation and Warehousing") label(9 "Information") label(10 "Finance and Insurance") label(11 "Real Estate and Rental and Leasing") label(12 "Professional, Scientific, and Technical Services") label(13 "Management of Companies and Enterprises") label (14 "Administrative, Support, Waste Management, Remediation Services") label(15 "Educational Services") label(16 "Health Care and Social Assistance") label(17 "Arts, Entertainment, and Recreation") label(18 "Accommodation and Food Services") label(19 "Other Services [except Public Administration]") label(20 "Public Administration") size(small)) saving(total_jobs_industry)
*graph export total_jobs_industry.jpg

graph bar (sum) cns04 cns07 cns15 cns16 cns18 cns20 if paradise == 1, over (year) title("Total Jobs per Industry")legend(label(1 "Construction") label(2 "Retail Trade") label(3 "Educational Services") label(4 "Health Care and Social Assistance") label(5 "Accommodation and Food Services")  label(6 "Public Administration") size(small)) 
graph export ${graphs}/total_jobs_industry_top6_rac.jpg, replace

*Change in jobs per race

graph bar (sum) cr01 cr02 cr03 cr04 cr05 cr07 if paradise == 1, over (year) title("Total Jobs per Race") legend (label(1 "White, Alone") label(2 "Black or African American Alone") label (3 "American Indian or Alaske Alone")label (4 "Asian Alone")label (5 "Native Hawaiian or PAcific Islander Alone")label (6 "Two or More Race Groups")size(small)) 
graph export ${graphs}/total_jobs_race_rac.jpg, replace
 
 
*Change in jobs per race excluding "white alone"

graph bar (sum) cr02 cr03 cr04 cr05 cr07 if paradise == 1, over (year) title("Total jobs per Race excluding 'White Alone'") legend (label(1 "Black or African American Alone") label (2 "American Indian or Alaske Alone")label (3 "Asian Alone")label (4 "Native Hawaiian or PAcific Islander Alone")label (5 "Two or More Race Groups") size(small)) 
graph export ${graphs}/total_jobs_race_sanswhite_rac.jpg, replace

 
*Change in jobs per Ethnicity 

graph bar (sum) ct01 ct02 if paradise == 1, over (year) title("Total Jobs per Ethnicity") legend (label(1 "Not Hispanic or Latino") label(2 "Hispanic or Latino")) 
graph export ${graphs}/total_jobs_ethnicity_rac.jpg, replace


*Change in jobs per Educational Attainment 
graph bar (sum) cd01 cd03 cd04 cd02 if paradise == 1, over (year) title("Total Jobs per Educational Attainment") legend (label(1 "Less than high school") label(2 "High School or equivalent") label(3 "Some College or associate") label(4 "Bachelor's degree or advance degree")size(small)) 
graph export ${graphs}/total_job_education_rac.jpg, replace


*Change in jobs per Sex 
graph bar (sum) cs01 cs02 if paradise == 1, over (year) title("Total Jobs per Sex") legend (label(1 "Male") label(2 "Female")) 
graph export ${graphs}/total_jobs_sex_rac.jpg, replace

***************************************************************************
*Bring in Work area data
use $data/wac_S000_JT00_2017.dta, clear
gen year=2017
append using $data/wac_S000_JT00_2018.dta
replace year=2018 if missing(year)
append using $data/wac_S000_JT00_2019.dta
replace year=2019 if missing(year)

*I think Paradise Census tracts are tracts 18,19, 20, 21 within Butte County
gen w_tract=substr(w_geocode,1,9)

gen paradise=0
replace paradise=1 if w_tract=="060070018"
replace paradise=1 if w_tract=="060070019"
replace paradise=1 if w_tract=="060070020"
replace paradise=1 if w_tract=="060070021"


** Total jobs by subgroup 


*Change in jobs per age group 
graph bar (sum) ca01 ca02 ca03 if paradise == 1, over (year) title("Total Jobs per age group") legend (label(1 "29 and younger") label(2 "30 to 54") label (3 "55 and older")) 
graph export ${graphs}/total_jobs_per_age_wac.jpg, replace

*Change in jobs per earnings

graph bar (sum) ce01 ce02 ce03 if paradise == 1, over (year) title("Total Jobs per Monthly Earnings") legend (label(1 "earnings $1250 or less") label(2 "earnings $1251 - $3333") label (3 "earnings greater than $3333") size(small)) 
graph export ${graphs}/total_jobs_earnings_wac.jpg, replace

*Change in jobs per idustry group (ALL)

*graph bar (sum) cns01 cns02 cns03 cns04 cns05 cns06 cns07 cns08 cns09 cns10 cns11 cns12 cns13 cns14 cns15 cns16 cns17 cns18 cns19 cns20 if paradise == 1, over (year) title("Total Jobs per Industry")legend(label(1 "Agriculture, Forestry, Fishing and Hunting") label(2 "Mining, Quarrying, and Oil and Gas Extraction") label(3 "Utilities") label(4 "Construction") label(5 "Manufacturing") label(6 "Wholesale Trade") label(7 "Retail Trade") label(8 "Transportation and Warehousing") label(9 "Information") label(10 "Finance and Insurance") label(11 "Real Estate and Rental and Leasing") label(12 "Professional, Scientific, and Technical Services") label(13 "Management of Companies and Enterprises") label (14 "Administrative, Support, Waste Management, Remediation Services") label(15 "Educational Services") label(16 "Health Care and Social Assistance") label(17 "Arts, Entertainment, and Recreation") label(18 "Accommodation and Food Services") label(19 "Other Services [except Public Administration]") label(20 "Public Administration") size(small)) saving(total_jobs_industry)
*graph export total_jobs_industry.jpg

graph bar (sum) cns04 cns07 cns15 cns16 cns18 cns20 if paradise == 1, over (year) title("Total Jobs per Industry")legend(label(1 "Construction") label(2 "Retail Trade") label(3 "Educational Services") label(4 "Health Care and Social Assistance") label(5 "Accommodation and Food Services")  label(6 "Public Administration") size(small)) 
graph export ${graphs}/total_jobs_industry_top6_wac.jpg, replace

*Change in jobs per wace

graph bar (sum) cr01 cr02 cr03 cr04 cr05 cr07 if paradise == 1, over (year) title("Total Jobs per wace") legend (label(1 "White, Alone") label(2 "Black or African American Alone") label (3 "American Indian or Alaske Alone")label (4 "Asian Alone")label (5 "Native Hawaiian or PAcific Islander Alone")label (6 "Two or More wace Groups")size(small)) 
graph export ${graphs}/total_jobs_wace_wac.jpg, replace
 
 
*Change in jobs per wace excluding "white alone"

graph bar (sum) cr02 cr03 cr04 cr05 cr07 if paradise == 1, over (year) title("Total jobs per race excluding 'White Alone'") legend (label(1 "Black or African American Alone") label (2 "American Indian or Alaske Alone")label (3 "Asian Alone")label (4 "Native Hawaiian or Pacific Islander Alone")label (5 "Two or More Race Groups") size(small)) 
graph export ${graphs}/total_jobs_race_sanswhite_wac.jpg, replace

 
*Change in jobs per Ethnicity 

graph bar (sum) ct01 ct02 if paradise == 1, over (year) title("Total Jobs per Ethnicity") legend (label(1 "Not Hispanic or Latino") label(2 "Hispanic or Latino")) 
graph export ${graphs}/total_jobs_ethnicity_wac.jpg, replace


*Change in jobs per Educational Attainment 
graph bar (sum) cd01 cd03 cd04 cd02 if paradise == 1, over (year) title("Total Jobs per Educational Attainment") legend (label(1 "Less than high school") label(2 "High School or equivalent") label(3 "Some College or associate") label(4 "Bachelor's degree or advance degree")size(small)) 
graph export ${graphs}/total_job_education_wac.jpg, replace


*Change in jobs per Sex 
graph bar (sum) cs01 cs02 if paradise == 1, over (year) title("Total Jobs per Sex") legend (label(1 "Male") label(2 "Female")) 
graph export ${graphs}/total_jobs_sex_wac.jpg, replace

log close

 

