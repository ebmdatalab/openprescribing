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
)

SELECT *
FROM practice
INNER JOIN ccg
  ON practice_month = ccg_month
INNER JOIN {measures}.global_data_{measure_id} AS global
  ON practice_month = global.month
