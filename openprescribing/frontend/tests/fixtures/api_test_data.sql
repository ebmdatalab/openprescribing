/*
 * This SQL script is used to populate the "materialised view" tables (ie.
 * those with the `vw__` prefix) during testing.  The queries used are
 * Postgres-ified versions of those in `frontend/management/commands/views_sql/`.
 * In production the queries are run against BigQuery.
*/

INSERT INTO
  vw__presentation_summary (
    processing_date, presentation_code, items, cost, quantity
  )
SELECT
  processing_date,
  presentation_code,
  SUM(total_items) AS items,
  SUM(actual_cost) AS cost,
  SUM(quantity)::int AS quantity
FROM
  frontend_prescription
GROUP BY
  processing_date,
  presentation_code
;

INSERT INTO
  vw__presentation_summary_by_ccg (
    processing_date, pct_id, presentation_code, items, cost, quantity
  )
SELECT
  processing_date,
  frontend_practice.ccg_id AS pct_id,
  presentation_code,
  SUM(total_items) AS items,
  SUM(actual_cost) AS cost,
  SUM(quantity)::int AS quantity
FROM
  frontend_prescription
JOIN
  frontend_practice
ON
  frontend_prescription.practice_id = frontend_practice.code
GROUP BY
  processing_date,
  frontend_practice.ccg_id,
  presentation_code
;

INSERT INTO
  vw__chemical_summary_by_ccg (
    processing_date, pct_id, chemical_id, items, cost, quantity
  )
SELECT
  processing_date,
  frontend_practice.ccg_id AS pct_id,
  SUBSTR(presentation_code, 1, 9) AS chemical_id,
  SUM(total_items) AS items,
  SUM(actual_cost) AS cost,
  SUM(quantity)::int AS quantity
FROM
  frontend_prescription
JOIN
  frontend_practice
ON
  frontend_prescription.practice_id = frontend_practice.code
GROUP BY
  processing_date,
  frontend_practice.ccg_id,
  chemical_id
;

INSERT INTO
  vw__chemical_summary_by_practice (
    processing_date, practice_id, chemical_id, items, cost, quantity
  )
SELECT
  processing_date,
  practice_id,
  SUBSTR(presentation_code, 1, 9) AS chemical_id,
  SUM(total_items) AS items,
  SUM(actual_cost) AS cost,
  SUM(quantity)::int AS quantity
FROM
  frontend_prescription
GROUP BY
  processing_date,
  practice_id,
  chemical_id
;

INSERT INTO
  vw__practice_summary (
    processing_date, practice_id, items, cost, quantity
  )
SELECT
  processing_date,
  practice_id,
  SUM(total_items) AS items,
  SUM(actual_cost) AS cost,
  SUM(quantity)::int AS quantity
FROM
  frontend_prescription
GROUP BY
  processing_date,
  practice_id
;

INSERT INTO
  vw__ccgstatistics (
    date, pct_id, name, total_list_size, astro_pu_items, astro_pu_cost, star_pu
  )
SELECT
  date,
  frontend_pct.code AS pct_id,
  frontend_pct.name AS name,
  SUM(total_list_size) AS total_list_size,
  SUM(astro_pu_items) AS astro_pu_items,
  SUM(astro_pu_cost) AS astro_pu_cost,
  jsonb_build_object(
    'analgesics_cost', SUM((star_pu->>'analgesics_cost')::float),
    'antidepressants_adq', SUM((star_pu->>'antidepressants_adq')::float),
    'antidepressants_cost', SUM((star_pu->>'antidepressants_cost')::float),
    'antiepileptic_drugs_cost', SUM((star_pu->>'antiepileptic_drugs_cost')::float),
    'antiplatelet_drugs_cost', SUM((star_pu->>'antiplatelet_drugs_cost')::float),
    'benzodiazepine_caps_and_tabs_cost', SUM((star_pu->>'benzodiazepine_caps_and_tabs_cost')::float),
    'bisphosphonates_and_other_drugs_cost', SUM((star_pu->>'bisphosphonates_and_other_drugs_cost')::float),
    'bronchodilators_cost', SUM((star_pu->>'bronchodilators_cost')::float),
    'calcium-channel_blockers_cost', SUM((star_pu->>'calcium-channel_blockers_cost')::float),
    'cox-2_inhibitors_cost', SUM((star_pu->>'cox-2_inhibitors_cost')::float),
    'drugs_acting_on_benzodiazepine_receptors_cost', SUM((star_pu->>'drugs_acting_on_benzodiazepine_receptors_cost')::float),
    'drugs_affecting_the_renin_angiotensin_system_cost', SUM((star_pu->>'drugs_affecting_the_renin_angiotensin_system_cost')::float),
    'drugs_for_dementia_cost', SUM((star_pu->>'drugs_for_dementia_cost')::float),
    'drugs_used_in_parkinsonism_and_related_disorders_cost', SUM((star_pu->>'drugs_used_in_parkinsonism_and_related_disorders_cost')::float),
    'hypnotics_adq', SUM((star_pu->>'hypnotics_adq')::float),
    'inhaled_corticosteroids_cost', SUM((star_pu->>'inhaled_corticosteroids_cost')::float),
    'laxatives_cost', SUM((star_pu->>'laxatives_cost')::float),
    'lipid-regulating_drugs_cost', SUM((star_pu->>'lipid-regulating_drugs_cost')::float),
    'omega-3_fatty_acid_compounds_adq', SUM((star_pu->>'omega-3_fatty_acid_compounds_adq')::float),
    'oral_antibacterials_cost', SUM((star_pu->>'oral_antibacterials_cost')::float),
    'oral_antibacterials_item', SUM((star_pu->>'oral_antibacterials_item')::float),
    'oral_nsaids_cost', SUM((star_pu->>'oral_nsaids_cost')::float),
    'proton_pump_inhibitors_cost', SUM((star_pu->>'proton_pump_inhibitors_cost')::float),
    'statins_cost', SUM((star_pu->>'statins_cost')::float),
    'ulcer_healing_drugs_cost', SUM((star_pu->>'ulcer_healing_drugs_cost')::float)
  ) AS star_pu
FROM
  frontend_practicestatistics
JOIN
  frontend_practice
ON
  frontend_practicestatistics.practice_id = frontend_practice.code
JOIN
  frontend_pct
ON
  frontend_practice.ccg_id = frontend_pct.code AND frontend_pct.org_type = 'CCG'
GROUP BY
  date,
  frontend_pct.code,
  frontend_pct.name
;
