SELECT
  local.numerator - global.regtm_10th * local.denominator AS cost_savings_10,
  local.numerator - global.regtm_20th * local.denominator AS cost_savings_20,
  local.numerator - global.regtm_30th * local.denominator AS cost_savings_30,
  local.numerator - global.regtm_40th * local.denominator AS cost_savings_40,
  local.numerator - global.regtm_50th * local.denominator AS cost_savings_50,
  local.numerator - global.regtm_60th * local.denominator AS cost_savings_60,
  local.numerator - global.regtm_70th * local.denominator AS cost_savings_70,
  local.numerator - global.regtm_80th * local.denominator AS cost_savings_80,
  local.numerator - global.regtm_90th * local.denominator AS cost_savings_90,
  local.*
FROM
  {measures}.regtm_data_{measure_id} AS local
LEFT JOIN
  {measures}.global_data_{measure_id} global
ON
  (global.month = local.month)
