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

