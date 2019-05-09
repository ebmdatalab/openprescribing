SELECT
  local.numerator - global.practice_10th * local.denominator AS cost_savings_10,
  local.numerator - global.practice_20th * local.denominator AS cost_savings_20,
  local.numerator - global.practice_30th * local.denominator AS cost_savings_30,
  local.numerator - global.practice_40th * local.denominator AS cost_savings_40,
  local.numerator - global.practice_50th * local.denominator AS cost_savings_50,
  local.numerator - global.practice_60th * local.denominator AS cost_savings_60,
  local.numerator - global.practice_70th * local.denominator AS cost_savings_70,
  local.numerator - global.practice_80th * local.denominator AS cost_savings_80,
  local.numerator - global.practice_90th * local.denominator AS cost_savings_90,
  local.*
FROM
  {measures}.practice_data_{measure_id} AS local
LEFT JOIN
  {measures}.global_data_{measure_id} global
ON
  (global.month = local.month)
