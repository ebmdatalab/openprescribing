-- This query selects deciles of calc_value by month from CCG-level
-- data, and adds this as new columns to the existing table that
-- includes practice-level data.
SELECT
  practice_deciles.month AS month,
  practice_deciles.denominator AS denominator,
  practice_deciles.numerator AS numerator,
  practice_deciles.practice_10th as practice_10th,
  practice_deciles.practice_20th as practice_20th,
  practice_deciles.practice_30th as practice_30th,
  practice_deciles.practice_40th as practice_40th,
  practice_deciles.practice_50th as practice_50th,
  practice_deciles.practice_60th as practice_60th,
  practice_deciles.practice_70th as practice_70th,
  practice_deciles.practice_80th as practice_80th,
  practice_deciles.practice_90th as practice_90th,
  ccg_deciles.ccg_10th as ccg_10th,
  ccg_deciles.ccg_20th as ccg_20th,
  ccg_deciles.ccg_30th as ccg_30th,
  ccg_deciles.ccg_40th as ccg_40th,
  ccg_deciles.ccg_50th as ccg_50th,
  ccg_deciles.ccg_60th as ccg_60th,
  ccg_deciles.ccg_70th as ccg_70th,
  ccg_deciles.ccg_80th as ccg_80th,
  ccg_deciles.ccg_90th as ccg_90th
  {extra_select_sql}
FROM {global_centiles_table} AS practice_deciles
LEFT JOIN (
SELECT
  month,
  MAX(p_10th) AS ccg_10th,
  MAX(p_20th) AS ccg_20th,
  MAX(p_30th) AS ccg_30th,
  MAX(p_40th) AS ccg_40th,
  MAX(p_50th) AS ccg_50th,
  MAX(p_60th) AS ccg_60th,
  MAX(p_70th) AS ccg_70th,
  MAX(p_80th) AS ccg_80th,
  MAX(p_90th) AS ccg_90th
FROM (
  SELECT
    month,
    PERCENTILE_CONT(0.1) OVER (PARTITION BY month ORDER BY {value_var} ASC) AS p_10th,
    PERCENTILE_CONT(0.2) OVER (PARTITION BY month ORDER BY {value_var} ASC) AS p_20th,
    PERCENTILE_CONT(0.3) OVER (PARTITION BY month ORDER BY {value_var} ASC) AS p_30th,
    PERCENTILE_CONT(0.4) OVER (PARTITION BY month ORDER BY {value_var} ASC) AS p_40th,
    PERCENTILE_CONT(0.5) OVER (PARTITION BY month ORDER BY {value_var} ASC) AS p_50th,
    PERCENTILE_CONT(0.6) OVER (PARTITION BY month ORDER BY {value_var} ASC) AS p_60th,
    PERCENTILE_CONT(0.7) OVER (PARTITION BY month ORDER BY {value_var} ASC) AS p_70th,
    PERCENTILE_CONT(0.8) OVER (PARTITION BY month ORDER BY {value_var} ASC) AS p_80th,
    PERCENTILE_CONT(0.9) OVER (PARTITION BY month ORDER BY {value_var} ASC) AS p_90th
  FROM {from_table}
  WHERE {value_var} IS NOT NULL)
  GROUP BY month) ccg_deciles
ON practice_deciles.month = ccg_deciles.month
