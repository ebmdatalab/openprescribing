-- 45s, 40GB, 78 million rows
SELECT
  month AS processing_date,
  pct AS pct_id,
  bnf_code AS presentation_code,
  SUM(items) AS items,
  SUM(actual_cost) AS cost,
  CAST(SUM(quantity) AS INT64) AS quantity
FROM
  ebmdatalab.%s.prescribing
GROUP BY
  processing_date,
  pct_id,
  presentation_code
