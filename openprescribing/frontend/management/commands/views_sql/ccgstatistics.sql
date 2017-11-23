-- This SQL is generated by `generate_ccg_statistics_sql.py`

CREATE TEMPORARY FUNCTION
  jsonify_starpu(analgesics_cost FLOAT64,antidepressants_adq FLOAT64,antidepressants_cost FLOAT64,antiepileptic_drugs_cost FLOAT64,antiplatelet_drugs_cost FLOAT64,benzodiazepine_caps_and_tabs_cost FLOAT64,bisphosphonates_and_other_drugs_cost FLOAT64,bronchodilators_cost FLOAT64,calcium_channel_blockers_cost FLOAT64,cox_2_inhibitors_cost FLOAT64,drugs_acting_on_benzodiazepine_receptors_cost FLOAT64,drugs_affecting_the_renin_angiotensin_system_cost FLOAT64,drugs_for_dementia_cost FLOAT64,drugs_used_in_parkinsonism_and_related_disorders_cost FLOAT64,hypnotics_adq FLOAT64,inhaled_corticosteroids_cost FLOAT64,laxatives_cost FLOAT64,lipid_regulating_drugs_cost FLOAT64,omega_3_fatty_acid_compounds_adq FLOAT64,oral_antibacterials_cost FLOAT64,oral_antibacterials_item FLOAT64,oral_nsaids_cost FLOAT64,proton_pump_inhibitors_cost FLOAT64,statins_cost FLOAT64,ulcer_healing_drugs_cost FLOAT64)
  RETURNS STRING
  LANGUAGE js AS '''
  var obj = {};
  obj['analgesics_cost'] = analgesics_cost;obj['antidepressants_adq'] = antidepressants_adq;obj['antidepressants_cost'] = antidepressants_cost;obj['antiepileptic_drugs_cost'] = antiepileptic_drugs_cost;obj['antiplatelet_drugs_cost'] = antiplatelet_drugs_cost;obj['benzodiazepine_caps_and_tabs_cost'] = benzodiazepine_caps_and_tabs_cost;obj['bisphosphonates_and_other_drugs_cost'] = bisphosphonates_and_other_drugs_cost;obj['bronchodilators_cost'] = bronchodilators_cost;obj['calcium-channel_blockers_cost'] = calcium_channel_blockers_cost;obj['cox-2_inhibitors_cost'] = cox_2_inhibitors_cost;obj['drugs_acting_on_benzodiazepine_receptors_cost'] = drugs_acting_on_benzodiazepine_receptors_cost;obj['drugs_affecting_the_renin_angiotensin_system_cost'] = drugs_affecting_the_renin_angiotensin_system_cost;obj['drugs_for_dementia_cost'] = drugs_for_dementia_cost;obj['drugs_used_in_parkinsonism_and_related_disorders_cost'] = drugs_used_in_parkinsonism_and_related_disorders_cost;obj['hypnotics_adq'] = hypnotics_adq;obj['inhaled_corticosteroids_cost'] = inhaled_corticosteroids_cost;obj['laxatives_cost'] = laxatives_cost;obj['lipid-regulating_drugs_cost'] = lipid_regulating_drugs_cost;obj['omega-3_fatty_acid_compounds_adq'] = omega_3_fatty_acid_compounds_adq;obj['oral_antibacterials_cost'] = oral_antibacterials_cost;obj['oral_antibacterials_item'] = oral_antibacterials_item;obj['oral_nsaids_cost'] = oral_nsaids_cost;obj['proton_pump_inhibitors_cost'] = proton_pump_inhibitors_cost;obj['statins_cost'] = statins_cost;obj['ulcer_healing_drugs_cost'] = ulcer_healing_drugs_cost
  return JSON.stringify(obj);
  ''';
SELECT
  month AS date,
  pct_id,
  ccgs.name AS name,
  SUM(total_list_size) AS total_list_size,
  SUM(astro_pu_items) AS astro_pu_items,
  SUM(astro_pu_cost) AS astro_pu_cost,
  jsonify_starpu(SUM(CAST(JSON_EXTRACT_SCALAR(star_pu,'$.analgesics_cost') AS FLOAT64)),SUM(CAST(JSON_EXTRACT_SCALAR(star_pu,'$.antidepressants_adq') AS FLOAT64)),SUM(CAST(JSON_EXTRACT_SCALAR(star_pu,'$.antidepressants_cost') AS FLOAT64)),SUM(CAST(JSON_EXTRACT_SCALAR(star_pu,'$.antiepileptic_drugs_cost') AS FLOAT64)),SUM(CAST(JSON_EXTRACT_SCALAR(star_pu,'$.antiplatelet_drugs_cost') AS FLOAT64)),SUM(CAST(JSON_EXTRACT_SCALAR(star_pu,'$.benzodiazepine_caps_and_tabs_cost') AS FLOAT64)),SUM(CAST(JSON_EXTRACT_SCALAR(star_pu,'$.bisphosphonates_and_other_drugs_cost') AS FLOAT64)),SUM(CAST(JSON_EXTRACT_SCALAR(star_pu,'$.bronchodilators_cost') AS FLOAT64)),SUM(CAST(JSON_EXTRACT_SCALAR(star_pu,'$.calcium-channel_blockers_cost') AS FLOAT64)),SUM(CAST(JSON_EXTRACT_SCALAR(star_pu,'$.cox-2_inhibitors_cost') AS FLOAT64)),SUM(CAST(JSON_EXTRACT_SCALAR(star_pu,'$.drugs_acting_on_benzodiazepine_receptors_cost') AS FLOAT64)),SUM(CAST(JSON_EXTRACT_SCALAR(star_pu,'$.drugs_affecting_the_renin_angiotensin_system_cost') AS FLOAT64)),SUM(CAST(JSON_EXTRACT_SCALAR(star_pu,'$.drugs_for_dementia_cost') AS FLOAT64)),SUM(CAST(JSON_EXTRACT_SCALAR(star_pu,'$.drugs_used_in_parkinsonism_and_related_disorders_cost') AS FLOAT64)),SUM(CAST(JSON_EXTRACT_SCALAR(star_pu,'$.hypnotics_adq') AS FLOAT64)),SUM(CAST(JSON_EXTRACT_SCALAR(star_pu,'$.inhaled_corticosteroids_cost') AS FLOAT64)),SUM(CAST(JSON_EXTRACT_SCALAR(star_pu,'$.laxatives_cost') AS FLOAT64)),SUM(CAST(JSON_EXTRACT_SCALAR(star_pu,'$.lipid-regulating_drugs_cost') AS FLOAT64)),SUM(CAST(JSON_EXTRACT_SCALAR(star_pu,'$.omega-3_fatty_acid_compounds_adq') AS FLOAT64)),SUM(CAST(JSON_EXTRACT_SCALAR(star_pu,'$.oral_antibacterials_cost') AS FLOAT64)),SUM(CAST(JSON_EXTRACT_SCALAR(star_pu,'$.oral_antibacterials_item') AS FLOAT64)),SUM(CAST(JSON_EXTRACT_SCALAR(star_pu,'$.oral_nsaids_cost') AS FLOAT64)),SUM(CAST(JSON_EXTRACT_SCALAR(star_pu,'$.proton_pump_inhibitors_cost') AS FLOAT64)),SUM(CAST(JSON_EXTRACT_SCALAR(star_pu,'$.statins_cost') AS FLOAT64)),SUM(CAST(JSON_EXTRACT_SCALAR(star_pu,'$.ulcer_healing_drugs_cost') AS FLOAT64))) AS star_pu
FROM
  hscic.practice_statistics AS statistics
JOIN hscic.ccgs ccgs
ON (statistics.pct_id = ccgs.code AND ccgs.org_type = 'CCG')
WHERE month > TIMESTAMP(DATE_SUB(DATE "{{this_month}}", INTERVAL 5 YEAR))
GROUP BY
  month,
  pct_id,
  name
