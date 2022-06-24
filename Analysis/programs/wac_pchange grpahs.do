clear
capture log close

**master set up 
macro drop _all
clear all
set more off
capture log close
set seed 39281

global today : di %tdCY.N.D date("$S_DATE", "DMY")

if c(username)=="Gabriela.Lahera"{
	global programs "C:\Users\Gabriela.Lahera\Documents\GitHub\ParadiseFire\Analysis\programs"
global data "C:\Users\Gabriela.Lahera\Documents\GitHub\ParadiseFire\Analysis\data"
	global output "C:\Users\Gabriela.Lahera\Documents\GitHub\ParadiseFire\Analysis\"
	global logs "C:\Users\Gabriela.Lahera\Documents\GitHub\ParadiseFire\Analysis\programs\logs"
}

cd $programs

**end 

use $data/wac_S000_JT00_2017.dta, clear
gen year=2017
append using $data/wac_S000_JT00_2018.dta
replace year=2018 if missing(year)
append using $data/wac_S000_JT00_2019.dta
replace year=2019 if missing(year)

*I think Paradise Census Tracts are tracts 18,19, 20, 21 within Butte County
gen h_tract=substr(w_geocode,1,9)
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



** Create bar two y-axis graph 

***********[reference]************
*Two Y-axes are not ideal, but necessary to get Paradise and Not Paradise on the same graph, at least while using the 5 geocodes
*graph twoway (connected c000 year if paradise==1, yaxis(1) ) (connected c000 year if paradise==0, yaxis(2)), xlabel(2017(1)2019) legend(label(1 "Paradise") label(2 "Rest of Butte County")) 
 
*graph twoway (connected c000_pctchg year if paradise==1) (connected c000_pctchg year if paradise==0), xlabel(2017(1)2019) legend(label(1 "Paradise") label(2 "Rest of Butte County"))

net install grc1leg, from (http://www.stata.com/users/vwiggins)

cd "C:\Users\Gabriela.Lahera\Documents\GitHub\ParadiseFire\Analysis\graphs\wac_pchange"

*Age
	graph twoway (connected ca01_pctchg year if paradise==1) (connected ca01_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) title(29 and Younger) legend(label(1 "Paradise") label(2 "Rest of Butte County")) saving(pctchg_age_1)
	graph twoway (connected ca02_pctchg year if paradise==1) (connected ca02_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title(30 to 54) saving(pctchg_age_2)
	graph twoway (connected ca03_pctchg year if paradise==1) (connected ca03_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title(55 and older) saving(pctchg_age_3)

grc1leg pctchg_age_1.gph pctchg_age_2.gph pctchg_age_3.gph, imargin(0 0 0 0) ycommon xcommon legendfrom(pctchg_age_1.gph) title("Percent Change of Jobs by Age 2017-2019", size(medium)) saving(wac_pctchg_age_2017-2019)
graph export wac_pctchg_age_2017-2019.jpg


*income
	graph twoway (connected ce01_pctchg year if paradise==1) (connected ce01_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) title("$1,250 or less")  legend(label(1 "Paradise") label(2 "Rest of Butte County")) saving(pctchg_income_1)
	graph twoway (connected ce02_pctchg year if paradise==1) (connected ce02_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("$1,251 to $3,333") saving(pctchg_income_2)
	graph twoway (connected ce03_pctchg year if paradise==1) (connected ce03_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("More than $3,333") saving(pctchg_income_3)


grc1leg pctchg_income_1.gph pctchg_income_2.gph pctchg_income_3.gph, imargin(0 0 0 0) ycommon xcommon legendfrom(pctchg_income_1.gph) title("Percent Change of Jobs by Monthly Income", size(medium)) saving(wac_pctchg_income_2017-2019)
graph export wac_pctchg_income_2017-2019.jpg
	
*industry
	graph twoway (connected cns04_pctchg year if paradise==1) (connected cns04_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Construction") saving(pctchg_industry_4)
	graph twoway (connected cns07_pctchg year if paradise==1) (connected cns07_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Retail Trade") saving(pctchg_industry_7)
	graph twoway (connected cns15_pctchg year if paradise==1) (connected cns15_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Educational Services") saving(pctchg_industry_15)
	graph twoway (connected cns16_pctchg year if paradise==1) (connected cns16_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Health Care ""& Social Assistance") saving (pctchg_industry_16)
	graph twoway (connected cns18_pctchg year if paradise==1) (connected cns18_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Accomodation ""& Food Services") saving(pctchg_industry_18)
	graph twoway (connected cns20_pctchg year if paradise==1) (connected cns20_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Public Administration ") saving(pctchg_industry_20)
	
	grc1leg pctchg_industry_4.gph pctchg_industry_7.gph pctchg_industry_15.gph pctchg_industry_16.gph pctchg_industry_18.gph pctchg_industry_20.gph, imargin(3 3 3 3) ycommon xcommon legendfrom(pctchg_industry_4.gph) title("Percent Change of Jobs by Industry (Top 6)", size(medium)) saving(wac_pctchg_industry_top6_2017-2019)
graph export wac_pctchg_industry_top6_2017-2019.jpg
	

*race
		graph twoway (connected cr01_pctchg year if paradise==1) (connected cr01_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("White Alone",size(medlarge)) saving(pctchg_race_1,replace)
		graph twoway (connected cr02_pctchg year if paradise==1) (connected cr02_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Black or ""African American Alone",size(medlarge)) saving(pctchg_race_2,replace)
		graph twoway (connected cr03_pctchg year if paradise==1) (connected cr03_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("American Indian or"" Alaska Native Alone",size(medlarge)) saving(pctchg_race_3)
		graph twoway (connected cr04_pctchg year if paradise==1) (connected cr04_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Asian Alone",size(medlarge)) saving(pctchg_race_4,replace)
		graph twoway (connected cr05_pctchg year if paradise==1) (connected cr05_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Native Hawaiian or"" Other Pacific Islander Alone",size(medlarge)) saving(pctchg_race_5,replace)
		graph twoway (connected cr07_pctchg year if paradise==1) (connected cr07_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Two or more"" Race groups",size(medlarge)) saving(pctchg_race_7,replace)
		

	grc1leg pctchg_race_1.gph pctchg_race_2.gph pctchg_race_3.gph pctchg_race_4.gph pctchg_race_5.gph pctchg_race_7.gph, imargin(3 3 3 3) ycommon xcommon legendfrom(pctchg_race_1.gph) title("Percent Change of Jobs by Race", size(medium)) saving(wac_pctchg_race_2017-2019,replace)
graph export wac_pctchg_race_2017-2019.jpg

*ethnicity
		graph twoway (connected ct01_pctchg year if paradise==1) (connected ct01_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Not Hispanic or Latino") saving(pctchg_ethnicity_1,replace)
		graph twoway (connected ct02_pctchg year if paradise==1) (connected ct02_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Not Hispanic or Latino") saving(pctchg_ethnicity_2,replace)
		
	grc1leg pctchg_ethnicity_1.gph pctchg_ethnicity_2.gph, imargin(3 3 2 2) ycommon xcommon legendfrom(pctchg_ethnicity_1.gph) title("Percent Change of Jobs by Race", size(medium)) saving(wac_pctchg_ethnicity_2017-2019,replace)
graph export wac_pctchg_ethnicity_2017-2019.jpg,replace
		
*Educational attainment 
	graph twoway (connected cd01_pctchg year if paradise==1) (connected cd01_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Less than high school") saving(pctchg_education_1,replace)
	graph twoway (connected cd02_pctchg year if paradise==1) (connected cd02_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("High scool or Equivalent") saving(pctchg_education_2,replace)
	graph twoway (connected cd03_pctchg year if paradise==1) (connected cd03_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Some College ""or Associate Degree") saving(pctchg_education_3,replace)
	graph twoway (connected cd04_pctchg year if paradise==1) (connected cd04_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Bachelor's Degree""or Advanced Degree") saving(pctchg_education_4,replace)

	grc1leg  pctchg_education_1.gph pctchg_education_2.gph pctchg_education_3.gph pctchg_education_4.gph, imargin(3 3 3 3) ycommon xcommon legendfrom(pctchg_education_1.gph) title("Percent Change of Jobs by Educational Attainment", size(medium)) saving(wac_pctchg_education_2017-2019,replace)
graph export wac_pctchg_education_2017-2019.jpg,replace
		
*Sex
	graph twoway (connected cs01_pctchg year if paradise==1) (connected cs01_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Male") saving(pctchg_sex_1,replace)
	graph twoway (connected cs02_pctchg year if paradise==1) (connected cs02_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Female") saving(pctchg_sex_2,replace)

	grc1leg  pctchg_sex_1.gph pctchg_sex_2.gph, imargin(2 2 0 0) ycommon xcommon legendfrom(pctchg_sex_1.gph) title("Percent Change of Jobs by Educational Attainment", size(medium)) saving(wac_pctchg_sex_2017-2019,replace)
graph export wac_pctchg_sex_2017-2019.jpg,replace
