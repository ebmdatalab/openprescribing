SELECT
  *
FROM (
  SELECT
    month,
    SUM(IF(cost_savings_10 > 0, cost_savings_10, 0)) AS cost_savings_10,
    SUM(IF(cost_savings_20 > 0, cost_savings_20, 0)) AS cost_savings_20,
    SUM(IF(cost_savings_30 > 0, cost_savings_30, 0)) AS cost_savings_30,
    SUM(IF(cost_savings_40 > 0, cost_savings_40, 0)) AS cost_savings_40,
    SUM(IF(cost_savings_50 > 0, cost_savings_50, 0)) AS cost_savings_50,
    SUM(IF(cost_savings_60 > 0, cost_savings_60, 0)) AS cost_savings_60,
    SUM(IF(cost_savings_70 > 0, cost_savings_70, 0)) AS cost_savings_70,
    SUM(IF(cost_savings_80 > 0, cost_savings_80, 0)) AS cost_savings_80,
    SUM(IF(cost_savings_90 > 0, cost_savings_90, 0)) AS cost_savings_90
  FROM
    {measures}.practice_data_{measure_id} GROUP BY month) AS practice,
  JOIN (
  SELECT
    month,
    SUM(IF(cost_savings_10 > 0, cost_savings_10, 0)) AS cost_savings_10,
    SUM(IF(cost_savings_20 > 0, cost_savings_20, 0)) AS cost_savings_20,
    SUM(IF(cost_savings_30 > 0, cost_savings_30, 0)) AS cost_savings_30,
    SUM(IF(cost_savings_40 > 0, cost_savings_40, 0)) AS cost_savings_40,
    SUM(IF(cost_savings_50 > 0, cost_savings_50, 0)) AS cost_savings_50,
    SUM(IF(cost_savings_60 > 0, cost_savings_60, 0)) AS cost_savings_60,
    SUM(IF(cost_savings_70 > 0, cost_savings_70, 0)) AS cost_savings_70,
    SUM(IF(cost_savings_80 > 0, cost_savings_80, 0)) AS cost_savings_80,
    SUM(IF(cost_savings_90 > 0, cost_savings_90, 0)) AS cost_savings_90
  FROM
    {measures}.ccg_data_{measure_id} GROUP BY month) ccg
  ON practice.month = ccg.month
  JOIN (SELECT * from {measures}.global_data_{measure_id}) global
  ON global.month = ccg.month
