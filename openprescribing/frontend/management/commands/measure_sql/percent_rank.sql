SELECT * FROM
  (
  SELECT
    *,
    PERCENT_RANK() * 100 OVER (PARTITION BY month ORDER BY {value_var}) AS percentile
  FROM
    {from_table}
  WHERE
    calc_value IS NOT NULL) a,
  (
  SELECT
    *,
    NULL AS percentile
  FROM
    {from_table}
  WHERE
    calc_value IS NULL) b
