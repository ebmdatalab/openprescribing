-- 45s, 40GB, 78 million rows
SELECT
  month AS processing_date,
  pct AS pct_id,
  bnf_code AS presentation_code,
  SUM(items) AS items,
  SUM(actual_cost) AS cost,
  CAST(SUM(quantity) AS INT64) AS quantity
FROM
  {hscic}.normalised_prescribing_standard
WHERE month > TIMESTAMP(DATE_SUB(DATE "{{this_month}}", INTERVAL 5 YEAR))
GROUP BY
  processing_date,
  pct_id,
  presentation_code
