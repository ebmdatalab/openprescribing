SELECT
  prescribing.sha AS sha,
  ccgs.regional_team_id AS regional_team,
  ccgs.stp_id AS stp,
  practices.ccg_id AS pct,
  prescribing.practice AS practice,
  TRIM(COALESCE(bnf_map.current_bnf_code, prescribing.bnf_code))
    AS bnf_code,
  TRIM(prescribing.bnf_name) AS bnf_name,
  prescribing.items AS items,
  prescribing.net_cost AS net_cost,
  prescribing.actual_cost AS actual_cost,
  prescribing.quantity AS quantity,
  prescribing.month AS month
FROM
  {project}.{hscic}.prescribing AS prescribing
LEFT JOIN
  {project}.{hscic}.bnf_map AS bnf_map
ON
  bnf_map.former_bnf_code = prescribing.bnf_code
INNER JOIN
  {project}.{hscic}.practices  AS practices
ON practices.code = prescribing.practice
INNER JOIN
  {project}.{hscic}.ccgs AS ccgs
ON practices.ccg_id = ccgs.code
