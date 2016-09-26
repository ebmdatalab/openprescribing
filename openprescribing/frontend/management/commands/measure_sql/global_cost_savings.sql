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
    {practice_table} GROUP BY month) AS practice,
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
    {ccg_table} GROUP BY month) ccg
  ON practice.month = ccg.month
  JOIN (SELECT * from {global_table}) global
  ON global.month = ccg.month
