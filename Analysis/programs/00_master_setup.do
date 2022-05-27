/***************************************
*Filename: 00_master_setup.do
*Purpose: Master file for the Paradise Fire research project.
* Sets file paths correctly for Dani's (c(username)=sandl305), and 
* Gabby's (c(username)=???) computers
*Created on: 5/27/2022
*Created by: Dani Sandler
*Modifications:
***************************************/

*front matter
macro drop _all
clear all
set more off
capture log close
set seed 39281

local today : di %tdCY.N.D date("$S_DATE", "DMY")

if c(username)=="sandl305"{
	global programs "C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\programs"
	global data "C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\data"
	global output "C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\"
	global logs "C:\Users\sandl305\Documents\GitHub\ParadiseFire\Analysis\programs\logs"
}

cd $programs