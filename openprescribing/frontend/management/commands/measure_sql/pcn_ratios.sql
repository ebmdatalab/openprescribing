SELECT
  pcn_id,
  month,
  SUM(numerator) AS numerator,
  SUM(denominator) AS denominator,
  IEEE_DIVIDE(SUM(numerator), SUM(denominator)) AS calc_value
  {denominator_aliases}
  {numerator_aliases}
FROM
  {measures}.practice_data_{measure_id}
GROUP BY
  pcn_id,
  month
ORDER BY
  month
