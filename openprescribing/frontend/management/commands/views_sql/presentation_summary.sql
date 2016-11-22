-- 36 seconds, 3.6GB
SELECT
  month AS processing_date,
  bnf_code AS presentation_code,
  SUM(items) AS items,
  SUM(actual_cost) AS cost,
  CAST(SUM(quantity) AS INT64) AS quantity
FROM
  ebmdatalab.%s.prescribing
GROUP BY
  processing_date,
  presentation_code
