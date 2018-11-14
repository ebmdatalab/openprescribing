-- This query selects deciles of calc_value by month from CCG-level
-- data, and adds this as new columns to the existing table that
-- includes practice-level data.
SELECT
  global_deciles.month AS month,
  global_deciles.denominator AS denominator,
  global_deciles.numerator AS numerator,
  global_deciles.practice_10th as practice_10th,
  global_deciles.practice_20th as practice_20th,
  global_deciles.practice_30th as practice_30th,
  global_deciles.practice_40th as practice_40th,
  global_deciles.practice_50th as practice_50th,
  global_deciles.practice_60th as practice_60th,
  global_deciles.practice_70th as practice_70th,
  global_deciles.practice_80th as practice_80th,
  global_deciles.practice_90th as practice_90th,
  global_deciles.ccg_10th as ccg_10th,
  global_deciles.ccg_20th as ccg_20th,
  global_deciles.ccg_30th as ccg_30th,
  global_deciles.ccg_40th as ccg_40th,
  global_deciles.ccg_50th as ccg_50th,
  global_deciles.ccg_60th as ccg_60th,
  global_deciles.ccg_70th as ccg_70th,
  global_deciles.ccg_80th as ccg_80th,
  global_deciles.ccg_90th as ccg_90th,
  stp_deciles.stp_10th as stp_10th,
  stp_deciles.stp_20th as stp_20th,
  stp_deciles.stp_30th as stp_30th,
  stp_deciles.stp_40th as stp_40th,
  stp_deciles.stp_50th as stp_50th,
  stp_deciles.stp_60th as stp_60th,
  stp_deciles.stp_70th as stp_70th,
  stp_deciles.stp_80th as stp_80th,
  stp_deciles.stp_90th as stp_90th
  {extra_select_sql}
FROM {measures}.global_data_{measure_id} AS global_deciles
LEFT JOIN (
  SELECT
    month,
    MAX(p_10th) AS stp_10th,
    MAX(p_20th) AS stp_20th,
    MAX(p_30th) AS stp_30th,
    MAX(p_40th) AS stp_40th,
    MAX(p_50th) AS stp_50th,
    MAX(p_60th) AS stp_60th,
    MAX(p_70th) AS stp_70th,
    MAX(p_80th) AS stp_80th,
    MAX(p_90th) AS stp_90th
  FROM (
      SELECT
        month,
        PERCENTILE_CONT(calc_value, 0.1) OVER (PARTITION BY month) AS p_10th,
        PERCENTILE_CONT(calc_value, 0.2) OVER (PARTITION BY month) AS p_20th,
        PERCENTILE_CONT(calc_value, 0.3) OVER (PARTITION BY month) AS p_30th,
        PERCENTILE_CONT(calc_value, 0.4) OVER (PARTITION BY month) AS p_40th,
        PERCENTILE_CONT(calc_value, 0.5) OVER (PARTITION BY month) AS p_50th,
        PERCENTILE_CONT(calc_value, 0.6) OVER (PARTITION BY month) AS p_60th,
        PERCENTILE_CONT(calc_value, 0.7) OVER (PARTITION BY month) AS p_70th,
        PERCENTILE_CONT(calc_value, 0.8) OVER (PARTITION BY month) AS p_80th,
        PERCENTILE_CONT(calc_value, 0.9) OVER (PARTITION BY month) AS p_90th
      FROM {measures}.stp_data_{measure_id}
      WHERE calc_value IS NOT NULL AND NOT IS_NAN(calc_value)
    )
    GROUP BY month
) AS stp_deciles
ON global_deciles.month = stp_deciles.month
