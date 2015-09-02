Notes on data sources
=====================

Notes on where data other than the HSCIC prescribing data is from.

HSCIC prescribing data
----------------------
Note integrity errors:
Missing chemical codes as already reported
Y04669 practice ID, present in T201407PDPI+BNFT_formatted.CSV but not in any of the practice tables

BNF codes
---------
Codes for BNF section names:
https://apps.nhsbsa.nhs.uk/infosystems/data/showDataSelector.do?reportId=126

CCGs, PCTs, SHAs, ATs
---------------------

NB HSCIC say that the codes used in the data are from Organisation Data Services:
http://systems.hscic.gov.uk/data/ods

For CCG and PCT information go here and search for PCT, CCG, Area Team:
https://geoportal.statistics.gov.uk/geoportal/catalog/main/home.page

Direct download link with three-letter and nine-letter codes and names:
https://geoportal.statistics.gov.uk/Docs/Names%20and%20Codes/Clinical_commissioning_groups_(Eng)_Apr_2013_Names_and_Codes.zip
There are 211 CCGs and they all have three-letter codes starting 0, 1 or 9.

For PCT-SHA and CCG-AT relation mapping search for:
Primary care organisations (2012) to strategic health authorities (2012) Eng lookup
Clinical commissioning groups (2013) to NHS area teams (2013) to NHS commissioning regions (2013) Eng lookup

Note: If you look in data/raw_data/T201304PDPI+BNFT.csv it starts with the CCG code 5D7 - which should no longer exist at that point. But that's because of people using old pads and/or prescriptions being cashed in late (they can be used for up to six months).

AT codes derived from here: http://www.ons.gov.uk/ons/guide-method/geography/geographic-policy/best-practice-guidance/presentation-order-guidance/health-areas/health-area-annex-b.xls

NB (not used): NHS postcode directory: http://www.datadictionary.nhs.uk/web_site_content/supporting_information/nhs_postcode_directory.asp?shownav=1

SHAs data (name and addresses, not boundaries):
http://systems.hscic.gov.uk/data/ods/datadownloads/haandsa

(Not used) GP practices:
http://systems.hscic.gov.uk/data/ods/datadownloads/gppractice

(Not used) Mapping GPs to CCGs - epraccur.csv:
http://data.gov.uk/dataset/england-nhs-connecting-for-health-organisation-data-service-data-files-of-general-medical-practices

Geographical data
-----------------

CCG KML boundaries from
http://www.england.nhs.uk/resources/ccg-maps/
Also generalised and clipped boundaries available from
https://geoportal.statistics.gov.uk/geoportal/catalog/main/home.page
(search for CCG, but not sure if these work)
The KML file says it's WGS84.

(Not used)
CCG boundaries: OGL licence
http://data.gov.uk/dataset/ccg-map

GP postcodes... TBA

GP level data: ASTRO PU and STAR PU
-----------------------------------
http://www.hscic.gov.uk/prescribing/measures has the weightings for 2009 and 2013. The actual link is here: http://www.hscic.gov.uk/media/13654/Prescribing-Units-2013/xls/PrescribingUnits2013.xlsx

Combine these with list data from NHS BSA Information Services Portal: https://apps.nhsbsa.nhs.uk/infosystems/welcome : then select Data > Demographic Data > Patient List Size Information and choose the National option

ASTRO PU is available in cost or item form: we use cost form for the moment.

STAR PUs are per condition, but should be easy to add.

(Alternatively, available here, which states that this data is OGL)
http://data.gov.uk/dataset/numbers_of_patients_registered_at_a_gp_practice

GP level data: QoF outcomes
---------------------------
TBA

Other outcomes:
- More than 300 of these
- Cover demographics, impact on NHS resources, patient survey results, screening levels, mortality...
- Published by HSCIC
http://data.gov.uk/dataset/gp-practice-data and see
https://indicators.ic.nhs.uk/webview/index.jsp?v=2&catalog=http%3A%2F%2Fhg-l-app-472.ic.green.net%3A80%2Fobj%2FfCatalog%2FCatalog77&submode=catalog&mode=documentation&top=yes

GP level data: Dispensing v non-dispensing practices
----------------------------------------------------
Use this: https://www.report.ppa.org.uk/ActProd1/getfolderitems.do?volume=actprod&userid=ciruser&password=foicir

Use the "Download link", choose "Excel Data" format and "All" items
http://www.hscic.gov.uk/article/2021/Website-Search?productid=17301&q=nhs+payments+gp&sort=Relevance&size=10&page=1&area=both#top
