SELECT
  ccgs.regional_team_id AS regional_team,
  ccgs.stp_id AS stp,
  practices.ccg_id AS pct,
  practices.pcn_id AS pcn,
  raw_prescribing.Practice_Code AS practice,
  COALESCE(bnf_map.current_bnf_code, raw_prescribing.BNF_Code)
    AS bnf_code,
  raw_prescribing.BNF_Description AS bnf_name,
  raw_prescribing.Items AS items,
  raw_prescribing.NIC AS net_cost,
  raw_prescribing.Actual_Cost AS actual_cost,
  raw_prescribing.Quantity AS quantity_per_item,
  raw_prescribing.Quantity * raw_prescribing.Items AS total_quantity,
  PARSE_DATETIME("%F", REGEXP_REPLACE(raw_prescribing._FILE_NAME, "^.+/(20\\d\\d)_(\\d\\d)/[^/]+$", "\\1-\\2-01")) AS month
FROM
  {project}.{hscic}.raw_prescribing AS raw_prescribing
LEFT JOIN
  {project}.{hscic}.bnf_map AS bnf_map
ON
  bnf_map.former_bnf_code = raw_prescribing.BNF_Code
INNER JOIN
  {project}.{hscic}.practices  AS practices
ON practices.code = raw_prescribing.Practice_Code
INNER JOIN
  {project}.{hscic}.ccgs AS ccgs
ON practices.ccg_id = ccgs.code
