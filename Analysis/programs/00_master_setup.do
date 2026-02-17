/***************************************
*Filename: 00_master_setup.do
*Purpose: Master file for the Paradise Fire research project.
* Sets file paths based on c(username). Add a new block for your username.
*Created on: 5/27/2022
*Modifications:
***************************************/

*front matter
macro drop _all
clear all
set more off
capture log close
set seed 39281

global today : di %tdCY.N.D date("$S_DATE", "DMY")

* Set paths based on username. Add your own block here.
* Example:
* if c(username)=="yourusername"{
*     global programs "C:\Users\yourusername\Documents\GitHub\ParadiseFire\Analysis\programs"
*     global data "C:\Users\yourusername\Documents\GitHub\ParadiseFire\Analysis\data"
*     global output "C:\Users\yourusername\Documents\GitHub\ParadiseFire\Analysis\"
*     global logs "C:\Users\yourusername\Documents\GitHub\ParadiseFire\Analysis\programs\logs"
*     global graphs "C:\Users\yourusername\Documents\GitHub\ParadiseFire\Analysis\graphs"
* }

display as error "ERROR: Set your username and paths in 00_master_setup.do"
exit 198




cd $programs