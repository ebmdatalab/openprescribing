SELECT * FROM
  (
  SELECT
    *,
    PERCENT_RANK() OVER (PARTITION BY month ORDER BY {value_var}) AS percentile
  FROM
    {from_table}
  WHERE
    calc_value IS NOT NULL AND NOT IS_NAN(calc_value)) a,
  (
  SELECT
    *,
    NULL AS percentile
  FROM
    {from_table}
  WHERE
    calc_value IS NULL OR IS_NAN(calc_value)) b
