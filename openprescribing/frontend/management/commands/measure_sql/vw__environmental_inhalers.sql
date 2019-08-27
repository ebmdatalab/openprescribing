-- This SQL is checked in to the git repo at measure_sql/vw__environmental_inhalers.sql.
-- Do not make changes directly in BQ!  Instead, change the version in the repo and run
--
--     ./manage.py create_bq_measure_views

SELECT
  presc.month,
  pct,
  practice,
  presc.bnf_code,
  form_route,
  items,
  quantity
FROM
  {project}.hscic.normalised_prescribing_standard AS presc
LEFT JOIN
  {project}.dmd.form_dose AS dmd
ON
  presc.bnf_code=dmd.bnf_code
WHERE
  presc.bnf_code LIKE "030%"
  AND (form_route="powderinhalation.inhalation"
    OR form_route= "pressurizedinhalation.inhalation")
GROUP BY
  month,
  pct,
  practice,
  bnf_code,
  form_route,
  items,
  quantity
