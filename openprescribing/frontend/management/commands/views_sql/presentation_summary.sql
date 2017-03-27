-- 36 seconds, 3.6GB
SELECT
  month AS processing_date,
  bnf_code AS presentation_code,
  SUM(items) AS items,
  SUM(actual_cost) AS cost,
  CAST(SUM(quantity) AS INT64) AS quantity
FROM
  ebmdatalab.{{dataset}}.normalised_prescribing
WHERE month > TIMESTAMP(DATE_SUB(DATE "{{this_month}}", INTERVAL 5 YEAR))
GROUP BY
  processing_date,
  presentation_code
