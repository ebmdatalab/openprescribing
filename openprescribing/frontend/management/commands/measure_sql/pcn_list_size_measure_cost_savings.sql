SELECT
  local.numerator - global.pcn_10th * local.denominator AS cost_savings_10,
  local.numerator - global.pcn_20th * local.denominator AS cost_savings_20,
  local.numerator - global.pcn_30th * local.denominator AS cost_savings_30,
  local.numerator - global.pcn_40th * local.denominator AS cost_savings_40,
  local.numerator - global.pcn_50th * local.denominator AS cost_savings_50,
  local.numerator - global.pcn_60th * local.denominator AS cost_savings_60,
  local.numerator - global.pcn_70th * local.denominator AS cost_savings_70,
  local.numerator - global.pcn_80th * local.denominator AS cost_savings_80,
  local.numerator - global.pcn_90th * local.denominator AS cost_savings_90,
  local.*
FROM
  {measures}.pcn_data_{measure_id} AS local
LEFT JOIN
  {measures}.global_data_{measure_id} global
ON
  (global.month = local.month)
