** Create Percent change variables for each subgroup 

*age
forvalues i = 1 / 3 {
	bysort paradise: egen ca0`i'_2017=max(ca0`i'*(year==2017))
 gen ca0`i'_pctchg=100*(ca0`i'-ca0`i'_2017)/ca0`i'_2017
}

*income
forvalues i = 1 / 3 {
 	bysort paradise: egen ce0`i'_2017=max(ce0`i'*(year==2017))
 gen ce0`i'_pctchg=100*(ce0`i'-ce0`i'_2017)/ce0`i'_2017
}

*industry pt 1
forvalues i = 1 / 9 {
	bysort paradise: egen cns0`i'_2017=max(cns0`i'*(year==2017))
 gen cns0`i'_pctchg=100*(cns0`i'-cns0`i'_2017)/cns0`i'_2017
}
 
 

*industry pt 2
forvalues i = 11 / 20 {
	bysort paradise: egen cns`i'_2017=max(cns`i'*(year==2017))
 gen cns`i'_pctchg=100*(cns`i'-cns`i'_2017)/cns`i'_2017
}

*race
forvalues i = 1 / 5 {
	bysort paradise: egen cr0`i'_2017=max(cr0`i'*(year==2017))
 gen cr0`i'_pctchg=100*(cr0`i'-cr0`i'_2017)/cr0`i'_2017
}
	bysort paradise: egen cr07_2017=max(cr07*(year==2017))
 gen cr07_pctchg=100*(cr07 - cr07_2017)/cr07_2017


*ethnicity
forvalues i = 1 / 2 {
	bysort paradise: egen ct0`i'_2017=max(ct0`i'*(year==2017))
 gen ct0`i'_pctchg=100*(ct0`i'-ct0`i'_2017)/ct0`i'_2017
}

*
forvalues i = 1 / 4 {
	bysort paradise: egen cd0`i'_2017=max(cd0`i'*(year==2017))
 gen cd0`i'_pctchg=100*(cd0`i'-cd0`i'_2017)/cd0`i'_2017
}

*
forvalues i = 1 / 2 {
	bysort paradise: egen cs0`i'_2017=max(cs0`i'*(year==2017))
 gen cs0`i'_pctchg=100*(cs0`i'-cs0`i'_2017)/cs0`i'_2017
}

** Create bar two y-axis graph 

***********[reference]************
*Two Y-axes are not ideal, but necessary to get Paradise and Not Paradise on the same graph, at least while using the 5 geocodes
*graph twoway (connected c000 year if paradise==1, yaxis(1) ) (connected c000 year if paradise==0, yaxis(2)), xlabel(2017(1)2019) legend(label(1 "Paradise") label(2 "Rest of Butte County")) 
 
*graph twoway (connected c000_pctchg year if paradise==1) (connected c000_pctchg year if paradise==0), xlabel(2017(1)2019) legend(label(1 "Paradise") label(2 "Rest of Butte County"))

net install grc1leg, from (http://www.stata.com/users/vwiggins)

cd "$graphs\pchange"

*Age
	graph twoway (connected ca01_pctchg year if paradise==1) (connected ca01_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) title(29 and Younger) legend(label(1 "Paradise") label(2 "Rest of Butte County")) saving(pctchg_age_1)
	graph twoway (connected ca02_pctchg year if paradise==1) (connected ca02_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title(30 to 54) saving(pctchg_age_2)
	graph twoway (connected ca03_pctchg year if paradise==1) (connected ca03_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title(55 and older) saving(pctchg_age_3)

grc1leg pctchg_age_1.gph pctchg_age_2.gph pctchg_age_3.gph, imargin(0 0 0 0) ycommon xcommon legendfrom(pctchg_age_1.gph) title("Percent Change of Jobs by Age 2017-2019", size(medium)) saving(pctchg_age_2017-2019)
graph export pctchg_age_2017-2019.jpg


*income
	graph twoway (connected ce01_pctchg year if paradise==1) (connected ce01_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) title("$1,250 or less")  legend(label(1 "Paradise") label(2 "Rest of Butte County")) saving(pctchg_income_1)
	graph twoway (connected ce02_pctchg year if paradise==1) (connected ce02_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("$1,251 to $3,333") saving(pctchg_income_2)
	graph twoway (connected ce03_pctchg year if paradise==1) (connected ce03_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("More than $3,333") saving(pctchg_income_3)


grc1leg pctchg_income_1.gph pctchg_income_2.gph pctchg_income_3.gph, imargin(0 0 0 0) ycommon xcommon legendfrom(pctchg_income_1.gph) title("Percent Change of Jobs by Monthly Income", size(medium)) saving(pctchg_income_2017-2019)
graph export pctchg_income_2017-2019.jpg
	
*industry
	graph twoway (connected cns04_pctchg year if paradise==1) (connected cns04_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Construction") saving(pctchg_industry_4)
	graph twoway (connected cns07_pctchg year if paradise==1) (connected cns07_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Retail Trade") saving(pctchg_industry_7)
	graph twoway (connected cns15_pctchg year if paradise==1) (connected cns15_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Educational Services") saving(pctchg_industry_15)
	graph twoway (connected cns16_pctchg year if paradise==1) (connected cns16_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Health Care ""& Social Assistance") saving (pctchg_industry_16)
	graph twoway (connected cns18_pctchg year if paradise==1) (connected cns18_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Accomodation ""& Food Services") saving(pctchg_industry_18)
	graph twoway (connected cns20_pctchg year if paradise==1) (connected cns20_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Public Administration ") saving(pctchg_industry_20)
	
	grc1leg pctchg_industry_4.gph pctchg_industry_7.gph pctchg_industry_15.gph pctchg_industry_16.gph pctchg_industry_18.gph pctchg_industry_20.gph, imargin(3 3 3 3) ycommon xcommon legendfrom(pctchg_industry_4.gph) title("Percent Change of Jobs by Industry (Top 6)", size(medium)) saving(pctchg_industry_top6_2017-2019)
graph export pctchg_industry_top6_2017-2019.jpg
	

*race
		graph twoway (connected cr01_pctchg year if paradise==1) (connected cr01_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("White Alone",size(medlarge)) saving(pctchg_race_1)
		graph twoway (connected cr02_pctchg year if paradise==1) (connected cr02_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Black or ""African American Alone",size(medlarge)) saving(pctchg_race_2)
		graph twoway (connected cr03_pctchg year if paradise==1) (connected cr03_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("American Indian or"" Alaska Native Alone",size(medlarge)) saving(pctchg_race_3)
		graph twoway (connected cr04_pctchg year if paradise==1) (connected cr04_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Asian Alone",size(medlarge)) saving(pctchg_race_4)
		graph twoway (connected cr05_pctchg year if paradise==1) (connected cr05_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Native Hawaiian or"" Other Pacific Islander Alone",size(medlarge)) saving(pctchg_race_5)
		graph twoway (connected cr07_pctchg year if paradise==1) (connected cr07_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Two or more"" Race groups",size(medlarge)) saving(pctchg_race_7)
		

	grc1leg pctchg_race_1.gph pctchg_race_2.gph pctchg_race_3.gph pctchg_race_4.gph pctchg_race_5.gph pctchg_race_7.gph, imargin(3 3 3 3) ycommon xcommon legendfrom(pctchg_race_1.gph) title("Percent Change of Jobs by Race", size(medium)) saving(pctchg_race_2017-2019,replace)
graph export pctchg_race_2017-2019.jpg

*ethnicity
		graph twoway (connected ct01_pctchg year if paradise==1) (connected ct01_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Not Hispanic or Latino") saving(pctchg_ethnicity_1)
		graph twoway (connected ct02_pctchg year if paradise==1) (connected ct02_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Not Hispanic or Latino") saving(pctchg_ethnicity_2)
		
	grc1leg pctchg_ethnicity_1.gph pctchg_ethnicity_2.gph, imargin(3 3 2 2) ycommon xcommon legendfrom(pctchg_ethnicity_1.gph) title("Percent Change of Jobs by Race", size(medium)) saving(pctchg_ethnicity_2017-2019)
graph export pctchg_ethnicity_2017-2019.jpg
		
*Educational attainment 
	graph twoway (connected cd01_pctchg year if paradise==1) (connected cd01_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Less than high school") saving(pctchg_education_1)
	graph twoway (connected cd02_pctchg year if paradise==1) (connected cd02_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("High scool or Equivalent") saving(pctchg_education_2)
	graph twoway (connected cd03_pctchg year if paradise==1) (connected cd03_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Some College ""or Associate Degree") saving(pctchg_education_3)
	graph twoway (connected cd04_pctchg year if paradise==1) (connected cd04_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Bachelor's Degree""or Advanced Degree") saving(pctchg_education_4)

	grc1leg  pctchg_education_1.gph pctchg_education_2.gph pctchg_education_3.gph pctchg_education_4.gph, imargin(3 3 3 3) ycommon xcommon legendfrom(pctchg_education_1.gph) title("Percent Change of Jobs by Educational Attainment", size(medium)) saving(pctchg_education_2017-2019)
graph export pctchg_education_2017-2019.jpg
		
*Sex
	graph twoway (connected cs01_pctchg year if paradise==1) (connected cs01_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Male") saving(pctchg_sex_1)
	graph twoway (connected cs02_pctchg year if paradise==1) (connected cs02_pctchg year if paradise==0), xlabel(2017(1)2019) ytitle(Percent change) legend(label(1 "Paradise") label(2 "Rest of Butte County")) title("Female") saving(pctchg_sex_2)

	grc1leg  pctchg_sex_1.gph pctchg_sex_2.gph, imargin(2 2 0 0) ycommon xcommon legendfrom(pctchg_sex_1.gph) title("Percent Change of Jobs by Educational Attainment", size(medium)) saving(pctchg_sex_2017-2019)
graph export pctchg_sex_2019.jpg

