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

log using $logs/difference_in_difference$today.log, replace


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

*create difference in difference variable
gen did = (year>2017)*paradise 

*control varibales 
gen age_pwork = ca02/c000
gen ed_hsplus = (cd02+cd03)/c000
gen ed_college = cd04/c000
gen p_female = cs02/c000

*run regressions (total jobs)
reg c000 paradise did i.year, r
reg c000 paradise did i.year age_pwork ed_hsplus ed_college p_female, r


****Run regressions per industry 
*Construction
reg cns04 paradise did i.year age_pwork ed_hsplus ed_college p_female, r
*Retail Trade 
reg cns07 paradise did i.year age_pwork ed_hsplus ed_college p_female, r
*Educational Services
reg cns15 paradise did i.year age_pwork ed_hsplus ed_college p_female, r 
*Health Care & Social Assistance 
reg cns16 paradise did i.year age_pwork ed_hsplus ed_college p_female, r
*Accomodation & Food Services 
reg cns18 paradise did i.year age_pwork ed_hsplus ed_college p_female, r
*Public Administration 
reg cns20 paradise did i.year age_pwork ed_hsplus ed_college p_female, r

****Run regressions per earnings 
*$1,250 or less
reg ce01 paradise did i.year age_pwork ed_hsplus ed_college  p_female, r
*$1,251 to $3,333
reg ce02 paradise did i.year age_pwork ed_hsplus ed_college  p_female, r
*more than $3,333
reg ce03 paradise did i.year age_pwork ed_hsplus ed_college p_female, r

