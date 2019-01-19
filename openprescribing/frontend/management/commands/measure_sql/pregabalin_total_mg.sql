-- This SQL is checked in to the git repo at measure_sql/pregabalin_total_mg.sql.
-- Do not make changes directly in BQ!  Instead, change the version in the repo and run
--
--     ./manage.py create_bq_measure_views

SELECT
  month,
  practice,
  pct,
  SUM(CASE
      WHEN SUBSTR(bnf_code,14,2)='AA' THEN quantity * 25
      WHEN SUBSTR(bnf_code,14,2)='AB' THEN quantity * 50
      WHEN SUBSTR(bnf_code,14,2)='AC' THEN quantity * 75
      WHEN SUBSTR(bnf_code,14,2)='AD' THEN quantity * 100
      WHEN SUBSTR(bnf_code,14,2)='AE' THEN quantity * 150
      WHEN SUBSTR(bnf_code,14,2)='AF' THEN quantity * 200
      WHEN SUBSTR(bnf_code,14,2)='AG' THEN quantity * 300
      WHEN SUBSTR(bnf_code,14,2)='AI' THEN quantity * 225
      WHEN SUBSTR(bnf_code,14,2)='AJ' THEN quantity * 30
      WHEN SUBSTR(bnf_code,14,2)='AK' THEN quantity * 40
      WHEN SUBSTR(bnf_code,14,2)='AM' THEN quantity * 5
      WHEN SUBSTR(bnf_code,14,2)='AH' THEN quantity * 15
      WHEN SUBSTR(bnf_code,14,2)='AN' THEN quantity * 20
      WHEN SUBSTR(bnf_code,14,2)='AQ' THEN quantity * 10
      WHEN SUBSTR(bnf_code,14,2)='AP' THEN quantity * 15
      WHEN SUBSTR(bnf_code,14,2)='AL' THEN quantity * 75
      ELSE 0 END) AS lyrica_mg
FROM
  {project}.{hscic}.normalised_prescribing_standard
WHERE
  bnf_code LIKE '0408010AE%'
GROUP BY
  month,
  practice,
  pct
