-- This SQL is checked in to the git repo at measure_sql/vw__opioids_total_dmd.sql.
-- Do not make changes directly in BQ!  Instead, change the version in the repo and run
--
--     ./manage.py create_bq_measure_views

#subquery to create a "simple" administration route. 
WITH 
simp_form AS ( 
SELECT DISTINCT vmp, #vmp code
                CASE 
                    WHEN descr LIKE '%injection%' THEN 'injection' #creates "injection" as route, regardless of whether injection or infusion. this also removes injection routes, e.g.
                    WHEN descr LIKE '%infusion%' THEN 'injection'  #s/c, i/v etc, AS often injections have many licensed routes, which would multiply the row
                    ELSE SUBSTR(form.descr, STRPOS(form.descr,".")+1) #takes the dosage form out of the string (e.g. tablet.oral) TO leave route.
                END AS simple_form 
FROM dmd.ont AS ont #the coded route for dosage form, includes vmp code 
INNER JOIN dmd.ontformroute AS form ON form.cd=ont.form #text description of route 
  )

#subquery to normalise strength to mg
,norm_vpi AS (
SELECT vmp, #vmp code
       ing, #ing code
       strnt_nmrtr_val, #numerator strength value
       strnt_nmrtr_uom, #numerator unit of measurement
       unit_num.descr AS unit_num, #numerator unit 
       unit_den.descr AS unit_den, #denominator unit
       CASE
           WHEN unit_num.descr = 'microgram' THEN vpi.strnt_nmrtr_val / 1000 #creates miligram value from mcg value
           WHEN unit_num.descr = 'gram' THEN vpi.strnt_nmrtr_val * 1000 #creates miligram value from gram value
           ELSE vpi.strnt_nmrtr_val
       END AS strnt_nmrtr_val_mg, #all listed drugs now in miligram rather than g or mcg
       CASE
           WHEN unit_den.descr = 'litre' THEN vpi.strnt_dnmtr_val * 1000 #some denominators listed as litre, so create mililitre value
           ELSE vpi.strnt_dnmtr_val
       END AS strnt_dnmtr_val_ml #denominator now in ml
FROM dmd.vpi AS vpi
LEFT JOIN dmd.unitofmeasure AS unit_num ON vpi.strnt_nmrtr_uom = unit_num.cd #join to create text value for numerator unit
LEFT JOIN dmd.unitofmeasure AS unit_den ON vpi.strnt_dnmtr_uom = unit_den.cd) #join to create text value for denominator unit

#subquery to create single BNF table for AMPs and VMPs
,vmp_amp AS 
(SELECT DISTINCT id,
                 nm,
                 bnf_code
FROM dmd.vmp #vmp table
WHERE bnf_code IS NOT NULL
UNION DISTINCT
SELECT DISTINCT vmp,
                nm,
                bnf_code
FROM dmd.amp #amp table
WHERE bnf_code IS NOT NULL)
    
#main query to calculate the OME
SELECT rx.month, 
       rx.practice, 
       rx.pct, 
       vpi.strnt_dnmtr_val_ml,
       sum(rx.quantity) as quantity,
       ing.id, #ingredient DM+D code. Combination products will have more than one ing code per VMP, e.g. co-codamol will have ing for paracetamoland codeine
       ing.nm, #ingredient name vmp.bnf_code AS bnf_code,
       vmp.nm AS vmp_nm, #VMP code
       vmp.bnf_code as bnf_code, #BNF code to link to prescribing data
       vpi.strnt_nmrtr_val_mg, #strength numerator in mg
       SUM(quantity*ome*(CASE
           WHEN ing.id=373492002 AND form.simple_form = 'transdermal' THEN (vpi.strnt_nmrtr_val_mg*72)/coalesce(vpi.strnt_dnmtr_val_ml, 1) # creates 72 hour dose for fentanyl transdermal patches, as doses are per hour on DM+D)
           WHEN ing.id=387173000 AND form.simple_form = 'transdermal' AND vpi.strnt_nmrtr_val IN (5, 10, 15, 20) THEN (vpi.strnt_nmrtr_val_mg*168)/coalesce(vpi.strnt_dnmtr_val_ml, 1) # creates 168 hour (7 day) dose for low-dose buprenorphine patch
           WHEN ing.id=387173000 AND form.simple_form = 'transdermal' AND vpi.strnt_nmrtr_val IN (35, 52.5, 70) THEN (vpi.strnt_nmrtr_val_mg*96)/coalesce(vpi.strnt_dnmtr_val_ml, 1) # creates 96 hour dose for higher-dose buprenorphine patch
           ELSE strnt_nmrtr_val_mg/coalesce(vpi.strnt_dnmtr_val_ml, 1) #all other products have usual dose - coalesce as solid dose forms do not have a denominator
       END)) AS ome_dose, 
       opioid.ome AS ome
FROM norm_vpi AS vpi #VPI has both ING and VMP codes in the table
INNER JOIN dmd.ing AS ing ON vpi.ing=ing.id #join to ING to get ING codes and name
INNER JOIN vmp_amp AS vmp ON vpi.vmp=vmp.id #join to get BNF codes for both VMPs and AMPs joined indirectly TO ING. 
INNER JOIN simp_form AS form ON vmp.id=form.vmp #join to subquery for simplified administration route
INNER JOIN richard.opioid_class AS opioid ON opioid.id=ing.id AND opioid.form=form.simple_form #join to OME table, which has OME value for ING/route pairs
INNER JOIN hscic.normalised_prescribing AS rx ON rx.bnf_code = vmp.bnf_code
WHERE rx.bnf_code NOT LIKE '0410%' #remove drugs used in opiate dependence
GROUP BY rx.month, 
         rx.practice, 
         rx.pct,
         id,
         ing.nm,
         vmp.bnf_code,
         vmp.nm,
         vpi.strnt_nmrtr_val,
         strnt_nmrtr_val_mg,
         vpi.strnt_dnmtr_val_ml,
         opioid.ome
