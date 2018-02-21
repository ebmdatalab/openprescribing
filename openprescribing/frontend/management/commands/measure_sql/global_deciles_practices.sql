SELECT
  month,
  MAX(p_10th) AS practice_10th,
  MAX(p_20th) AS practice_20th,
  MAX(p_30th) AS practice_30th,
  MAX(p_40th) AS practice_40th,
  MAX(p_50th) AS practice_50th,
  MAX(p_60th) AS practice_60th,
  MAX(p_70th) AS practice_70th,
  MAX(p_80th) AS practice_80th,
  MAX(p_90th) AS practice_90th,
  SUM(denominator) AS denominator,
  SUM(numerator) AS numerator
  {extra_select_sql}
FROM (
  SELECT
    *,
    PERCENTILE_CONT(0.1) OVER (PARTITION BY month ORDER BY calc_value ASC) AS p_10th,
    PERCENTILE_CONT(0.2) OVER (PARTITION BY month ORDER BY calc_value ASC) AS p_20th,
    PERCENTILE_CONT(0.3) OVER (PARTITION BY month ORDER BY calc_value ASC) AS p_30th,
    PERCENTILE_CONT(0.4) OVER (PARTITION BY month ORDER BY calc_value ASC) AS p_40th,
    PERCENTILE_CONT(0.5) OVER (PARTITION BY month ORDER BY calc_value ASC) AS p_50th,
    PERCENTILE_CONT(0.6) OVER (PARTITION BY month ORDER BY calc_value ASC) AS p_60th,
    PERCENTILE_CONT(0.7) OVER (PARTITION BY month ORDER BY calc_value ASC) AS p_70th,
    PERCENTILE_CONT(0.8) OVER (PARTITION BY month ORDER BY calc_value ASC) AS p_80th,
    PERCENTILE_CONT(0.9) OVER (PARTITION BY month ORDER BY calc_value ASC) AS p_90th
  FROM {measures}.practice_data_{measure_id}
  WHERE calc_value IS NOT NULL AND NOT IS_NAN(calc_value)) a,
  (SELECT
    *,
  FROM {measures}.practice_data_{measure_id}
  WHERE calc_value IS NULL OR IS_NAN(calc_value)) b
  GROUP BY month
