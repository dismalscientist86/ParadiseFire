** Total jobs by subgroup 

cd "$graphs"
*Change in jobs per age group 
graph bar (sum) ca01 ca02 ca03 if paradise == 1, over (year) title("Total Jobs per age group") legend (label(1 "29 and younger") label(2 "30 to 54") label (3 "55 and older")) saving(total_jobs_per_age)
graph export total_jobs_per_age.jpg

*Change in jobs per earnings

graph bar (sum) ce01 ce02 ce03 if paradise == 1, over (year) title("Total Jobs per Monthly Earnings") legend (label(1 "earnings $1250 or less") label(2 "earnings $1251 - $3333") label (3 "earnings greater than $3333") size(small)) saving(total_jobs_earnings)
graph export total_jobs_earnings.jpg

*Change in jobs per idustry group (ALL)

*graph bar (sum) cns01 cns02 cns03 cns04 cns05 cns06 cns07 cns08 cns09 cns10 cns11 cns12 cns13 cns14 cns15 cns16 cns17 cns18 cns19 cns20 if paradise == 1, over (year) title("Total Jobs per Industry")legend(label(1 "Agriculture, Forestry, Fishing and Hunting") label(2 "Mining, Quarrying, and Oil and Gas Extraction") label(3 "Utilities") label(4 "Construction") label(5 "Manufacturing") label(6 "Wholesale Trade") label(7 "Retail Trade") label(8 "Transportation and Warehousing") label(9 "Information") label(10 "Finance and Insurance") label(11 "Real Estate and Rental and Leasing") label(12 "Professional, Scientific, and Technical Services") label(13 "Management of Companies and Enterprises") label (14 "Administrative, Support, Waste Management, Remediation Services") label(15 "Educational Services") label(16 "Health Care and Social Assistance") label(17 "Arts, Entertainment, and Recreation") label(18 "Accommodation and Food Services") label(19 "Other Services [except Public Administration]") label(20 "Public Administration") size(small)) saving(total_jobs_industry)
*graph export total_jobs_industry.jpg

graph bar (sum) cns04 cns07 cns15 cns16 cns18 cns20 if paradise == 1, over (year) title("Total Jobs per Industry")legend(label(1 "Construction") label(2 "Retail Trade") label(3 "Educational Services") label(4 "Health Care and Social Assistance") label(5 "Accommodation and Food Services")  label(6 "Public Administration") size(small)) saving(total_jobs_industry_top6)
graph export total_jobs_industry_top6.jpg

*Change in jobs per race

graph bar (sum) cr01 cr02 cr03 cr04 cr05 cr07 if paradise == 1, over (year) title("Total Jobs per Race") legend (label(1 "White, Alone") label(2 "Black or African American Alone") label (3 "American Indian or Alaske Alone")label (4 "Asian Alone")label (5 "Native Hawaiian or PAcific Islander Alone")label (6 "Two or More Race Groups")size(small)) saving(total_jobs_race)
graph export total_jobs_race.jpg
 
 
*Change in jobs per race excluding "white alone"

graph bar (sum) cr02 cr03 cr04 cr05 cr07 if paradise == 1, over (year) title("Total jobs per Race excluding 'White Alone'") legend (label(1 "Black or African American Alone") label (2 "American Indian or Alaske Alone")label (3 "Asian Alone")label (4 "Native Hawaiian or PAcific Islander Alone")label (5 "Two or More Race Groups") size(small)) saving(total_jobs_race_sanswhite)
graph export total_jobs_race_sanswhite.jpg

 
*Change in jobs per Ethnicity 

graph bar (sum) ct01 ct02 if paradise == 1, over (year) title("Total Jobs per Ethnicity") legend (label(1 "Not Hispanic or Latino") label(2 "Hispanic or Latino")) saving(total_jobs_ethnicity)
graph export total_jobs_ethnicity.jpg


*Change in jobs per Educational Attainment 
graph bar (sum) cd01 cd03 cd04 cd02 if paradise == 1, over (year) title("Total Jobs per Educational Attainment") legend (label(1 "Less than high school") label(2 "High School or equivalent") label(3 "Some College or associate") label(4 "Bachelor's degree or advance degree")size(small)) saving(total_jobs_education)
graph export total_job_education.jpg


*Change in jobs per Sex 
graph bar (sum) cs01 cs02 if paradise == 1, over (year) title("Total Jobs per Sex") legend (label(1 "Male") label(2 "Female")) saving(total_jobs_sex)
graph export total_jobs_sex.jpg
 

