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
  global_deciles.pcn_10th as pcn_10th,
  global_deciles.pcn_20th as pcn_20th,
  global_deciles.pcn_30th as pcn_30th,
  global_deciles.pcn_40th as pcn_40th,
  global_deciles.pcn_50th as pcn_50th,
  global_deciles.pcn_60th as pcn_60th,
  global_deciles.pcn_70th as pcn_70th,
  global_deciles.pcn_80th as pcn_80th,
  global_deciles.pcn_90th as pcn_90th,
  global_deciles.ccg_10th as ccg_10th,
  global_deciles.ccg_20th as ccg_20th,
  global_deciles.ccg_30th as ccg_30th,
  global_deciles.ccg_40th as ccg_40th,
  global_deciles.ccg_50th as ccg_50th,
  global_deciles.ccg_60th as ccg_60th,
  global_deciles.ccg_70th as ccg_70th,
  global_deciles.ccg_80th as ccg_80th,
  global_deciles.ccg_90th as ccg_90th,
  global_deciles.stp_10th as stp_10th,
  global_deciles.stp_20th as stp_20th,
  global_deciles.stp_30th as stp_30th,
  global_deciles.stp_40th as stp_40th,
  global_deciles.stp_50th as stp_50th,
  global_deciles.stp_60th as stp_60th,
  global_deciles.stp_70th as stp_70th,
  global_deciles.stp_80th as stp_80th,
  global_deciles.stp_90th as stp_90th,
  regtm_deciles.regtm_10th as regtm_10th,
  regtm_deciles.regtm_20th as regtm_20th,
  regtm_deciles.regtm_30th as regtm_30th,
  regtm_deciles.regtm_40th as regtm_40th,
  regtm_deciles.regtm_50th as regtm_50th,
  regtm_deciles.regtm_60th as regtm_60th,
  regtm_deciles.regtm_70th as regtm_70th,
  regtm_deciles.regtm_80th as regtm_80th,
  regtm_deciles.regtm_90th as regtm_90th
  {extra_select_sql}
FROM {measures}.global_data_{measure_id} AS global_deciles
LEFT JOIN (
  SELECT
    month,
    MAX(p_10th) AS regtm_10th,
    MAX(p_20th) AS regtm_20th,
    MAX(p_30th) AS regtm_30th,
    MAX(p_40th) AS regtm_40th,
    MAX(p_50th) AS regtm_50th,
    MAX(p_60th) AS regtm_60th,
    MAX(p_70th) AS regtm_70th,
    MAX(p_80th) AS regtm_80th,
    MAX(p_90th) AS regtm_90th
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
      FROM {measures}.regtm_data_{measure_id}
      WHERE calc_value IS NOT NULL AND NOT IS_NAN(calc_value)
    )
    GROUP BY month
) AS regtm_deciles
ON global_deciles.month = regtm_deciles.month
