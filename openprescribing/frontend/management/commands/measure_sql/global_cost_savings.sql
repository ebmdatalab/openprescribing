WITH practice AS (
  SELECT
    month AS practice_month,
    SUM(IF(cost_savings_10 > 0, cost_savings_10, 0)) AS practice_cost_savings_10,
    SUM(IF(cost_savings_20 > 0, cost_savings_20, 0)) AS practice_cost_savings_20,
    SUM(IF(cost_savings_30 > 0, cost_savings_30, 0)) AS practice_cost_savings_30,
    SUM(IF(cost_savings_40 > 0, cost_savings_40, 0)) AS practice_cost_savings_40,
    SUM(IF(cost_savings_50 > 0, cost_savings_50, 0)) AS practice_cost_savings_50,
    SUM(IF(cost_savings_60 > 0, cost_savings_60, 0)) AS practice_cost_savings_60,
    SUM(IF(cost_savings_70 > 0, cost_savings_70, 0)) AS practice_cost_savings_70,
    SUM(IF(cost_savings_80 > 0, cost_savings_80, 0)) AS practice_cost_savings_80,
    SUM(IF(cost_savings_90 > 0, cost_savings_90, 0)) AS practice_cost_savings_90
  FROM
    {measures}.practice_data_{measure_id} GROUP BY month
),

ccg AS (
  SELECT
    month AS ccg_month,
    SUM(IF(cost_savings_10 > 0, cost_savings_10, 0)) AS ccg_cost_savings_10,
    SUM(IF(cost_savings_20 > 0, cost_savings_20, 0)) AS ccg_cost_savings_20,
    SUM(IF(cost_savings_30 > 0, cost_savings_30, 0)) AS ccg_cost_savings_30,
    SUM(IF(cost_savings_40 > 0, cost_savings_40, 0)) AS ccg_cost_savings_40,
    SUM(IF(cost_savings_50 > 0, cost_savings_50, 0)) AS ccg_cost_savings_50,
    SUM(IF(cost_savings_60 > 0, cost_savings_60, 0)) AS ccg_cost_savings_60,
    SUM(IF(cost_savings_70 > 0, cost_savings_70, 0)) AS ccg_cost_savings_70,
    SUM(IF(cost_savings_80 > 0, cost_savings_80, 0)) AS ccg_cost_savings_80,
    SUM(IF(cost_savings_90 > 0, cost_savings_90, 0)) AS ccg_cost_savings_90
  FROM
    {measures}.ccg_data_{measure_id} GROUP BY month
),

stp AS (
  SELECT
    month AS stp_month,
    SUM(IF(cost_savings_10 > 0, cost_savings_10, 0)) AS stp_cost_savings_10,
    SUM(IF(cost_savings_20 > 0, cost_savings_20, 0)) AS stp_cost_savings_20,
    SUM(IF(cost_savings_30 > 0, cost_savings_30, 0)) AS stp_cost_savings_30,
    SUM(IF(cost_savings_40 > 0, cost_savings_40, 0)) AS stp_cost_savings_40,
    SUM(IF(cost_savings_50 > 0, cost_savings_50, 0)) AS stp_cost_savings_50,
    SUM(IF(cost_savings_60 > 0, cost_savings_60, 0)) AS stp_cost_savings_60,
    SUM(IF(cost_savings_70 > 0, cost_savings_70, 0)) AS stp_cost_savings_70,
    SUM(IF(cost_savings_80 > 0, cost_savings_80, 0)) AS stp_cost_savings_80,
    SUM(IF(cost_savings_90 > 0, cost_savings_90, 0)) AS stp_cost_savings_90
  FROM
    {measures}.stp_data_{measure_id} GROUP BY month
),

global AS (
  SELECT
    month AS global_month,
    cost_per_denom AS global_cost_per_denom,
    cost_per_num AS global_cost_per_num,
    denom_cost AS global_denom_cost,
    denom_items AS global_denom_items,
    denom_quantity AS global_denom_quantity,
    denominator AS global_denominator,
    num_cost AS global_num_cost,
    num_items AS global_num_items,
    num_quantity AS global_num_quantity,
    numerator AS global_numerator,
    stp_10th AS global_stp_10th,
    stp_20th AS global_stp_20th,
    stp_30th AS global_stp_30th,
    stp_40th AS global_stp_40th,
    stp_50th AS global_stp_50th,
    stp_60th AS global_stp_60th,
    stp_70th AS global_stp_70th,
    stp_80th AS global_stp_80th,
    stp_90th AS global_stp_90th,
    ccg_10th AS global_ccg_10th,
    ccg_20th AS global_ccg_20th,
    ccg_30th AS global_ccg_30th,
    ccg_40th AS global_ccg_40th,
    ccg_50th AS global_ccg_50th,
    ccg_60th AS global_ccg_60th,
    ccg_70th AS global_ccg_70th,
    ccg_80th AS global_ccg_80th,
    ccg_90th AS global_ccg_90th,
    practice_10th AS global_practice_10th,
    practice_20th AS global_practice_20th,
    practice_30th AS global_practice_30th,
    practice_40th AS global_practice_40th,
    practice_50th AS global_practice_50th,
    practice_60th AS global_practice_60th,
    practice_70th AS global_practice_70th,
    practice_80th AS global_practice_80th,
    practice_90th AS global_practice_90th
  FROM
    {measures}.global_data_{measure_id}
)

SELECT *
FROM practice
INNER JOIN ccg
  ON practice_month = ccg_month
INNER JOIN stp
  ON practice_month = stp_month
INNER JOIN global
  ON practice_month = global_month
