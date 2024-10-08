SELECT
  pct_id,
  ccgs.stp_id AS stp_id,
  ccgs.regional_team_id AS regional_team_id,
  month,
  SUM(numerator) AS numerator,
  SUM(denominator) AS denominator,
  IEEE_DIVIDE(SUM(numerator), SUM(denominator)) AS calc_value
  {denominator_aliases}
  {numerator_aliases}
FROM
  {measures}.practice_data_{measure_id}
JOIN {hscic}.ccgs AS ccgs
ON (ccgs.code = pct_id AND ccgs.org_type = 'CCG')
GROUP BY
  regional_team_id,
  stp_id,
  pct_id,
  month
ORDER BY
  month
