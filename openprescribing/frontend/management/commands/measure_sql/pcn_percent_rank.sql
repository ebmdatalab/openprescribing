SELECT
  *,
  PERCENT_RANK() OVER (PARTITION BY month ORDER BY calc_value) AS percentile
FROM
  {measures}.pcn_data_{measure_id}
WHERE
  calc_value IS NOT NULL AND NOT IS_NAN(calc_value)

UNION ALL

SELECT
  *,
  NULL AS percentile
FROM
  {measures}.pcn_data_{measure_id}
WHERE
  calc_value IS NULL OR IS_NAN(calc_value)
