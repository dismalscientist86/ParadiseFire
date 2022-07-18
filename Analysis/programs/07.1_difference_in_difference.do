******* Regressions with 2019 paradise as treatment 

clear
capture log close

if c(username)=="sandl305"{
	do "C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\programs\00_master_setup.do"
}
if c(username)!="sandl305"{
	do "C:\Users\Gabriela.Lahera\Documents\GitHub\ParadiseFire\Analysis\programs\00_master_setup.do"
}

 use $data/wac_2013_2019.dta
*create difference in difference variable
gen did = (year>2018)*paradise 

*control variables (2017 levels)
bysort w_geocode: egen c000_2018=max(c000*(year==2018))
bysort w_geocode: egen ca02_2018=max(ca02*(year==2018))
bysort w_geocode: egen cd02_2018=max(cd02*(year==2018))
bysort w_geocode: egen cd03_2018=max(cd03*(year==2018))
bysort w_geocode: egen cd04_2018=max(cd04*(year==2018))
bysort w_geocode: egen cs02_2018=max(cs02*(year==2018))
gen age_pwork = ca02_2018/c000_2018
gen ed_hsplus = (cd02_2018+cd03_2018)/c000_2018
gen ed_college = cd04_2018/c000_2018
gen p_female = cs02_2018/c000_2018

*run regressions (total jobs)
reg c000 did paradise i.year, r
eststo all: reg c000 did paradise i.year age_pwork ed_hsplus ed_college p_female, r


****Run regressions per industry 
*Construction
eststo const: reg cns04 did paradise i.year age_pwork ed_hsplus ed_college p_female, r
*Retail Trade 
eststo retail: reg cns07 did paradise i.year age_pwork ed_hsplus ed_college p_female, r
*Educational Services
eststo edu: reg cns15 did paradise i.year age_pwork ed_hsplus ed_college p_female, r 
*Health Care & Social Assistance 
eststo health: reg cns16 did paradise i.year age_pwork ed_hsplus ed_college p_female, r
*Accomodation & Food Services 
eststo food: reg cns18 did paradise i.year age_pwork ed_hsplus ed_college p_female, r
*Public Administration 
eststo public: reg cns20 did paradise i.year age_pwork ed_hsplus ed_college p_female, r

****Run regressions per earnings 
*$1,250 or less
eststo low: reg ce01 did paradise i.year age_pwork ed_hsplus ed_college  p_female, r
*$1,251 to $3,333
eststo medium: reg ce02 did paradise i.year age_pwork ed_hsplus ed_college  p_female, r
*more than $3,333
eststo high: reg ce03 did paradise i.year age_pwork ed_hsplus ed_college p_female, r

esttab all const retail edu health food public using $output\tables\industry_test.csv, replace nonum drop(*year) mtitles("All" "Construction" "Retail" "Education" "Healthcare" "Accomodation & Food" "Public Administration") varlabel(paradise "Paradise" did "Post-Fire" age_pwork "% Prime-Age" ed_hsplus "% High School" ed_college "% College" p_female "% Female" )

esttab all low medium high using $output\tables\earnings_test.csv, replace nonum drop(*year) mtitles("All" "Low Earnings" "Medium Earnings" "High Earnings") varlabel(paradise "Paradise" did "Post-Fire" age_pwork "% Prime-Age" ed_hsplus "% High School" ed_college "% College" p_female "% Female" )
