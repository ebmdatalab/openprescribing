SELECT
  *,
  PERCENT_RANK() OVER (PARTITION BY month ORDER BY calc_value) AS percentile
FROM (
  SELECT
    pct_id,
    month,
    SUM(numerator) AS numerator,
    SUM(denominator) AS denominator,
    SUM(numerator)/SUM(denominator) AS calc_value
    {denominator_aliases}
    {numerator_aliases}
  FROM
    {from_table}
  GROUP BY
    pct_id,
    month
  ORDER BY
    month )
