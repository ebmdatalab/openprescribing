-- 45s, 40GB, 78 million rows
SELECT
  month AS processing_date,
  practices.ccg_id AS pct_id,
  bnf_code AS presentation_code,
  SUM(items) AS items,
  SUM(actual_cost) AS cost,
  CAST(SUM(quantity) AS INT64) AS quantity
FROM
  {hscic}.normalised_prescribing_standard
INNER JOIN {hscic}.practices
  ON normalised_prescribing_standard.practice = practices.code
WHERE month > TIMESTAMP(DATE_SUB(DATE "{{this_month}}", INTERVAL 5 YEAR))
GROUP BY
  processing_date,
  practices.ccg_id,
  presentation_code
