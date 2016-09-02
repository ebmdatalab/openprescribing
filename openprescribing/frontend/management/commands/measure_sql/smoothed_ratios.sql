SELECT
  *,
  COALESCE(numerator / denominator, 0) AS raw_ratio,
  COALESCE(numerator_in_window / denominator_in_window, 0) AS smoothed_ratio,
  PERCENT_RANK() OVER (PARTITION BY month ORDER BY smoothed_ratio) AS percentile
FROM (
  SELECT
    *,
    DATE(month) AS month_fmt,
    SUM(numerator) OVER (PARTITION BY practice ORDER BY month RANGE BETWEEN 1000000*3600*24*31*2 PRECEDING AND CURRENT ROW) AS numerator_in_window,
    SUM(denominator) OVER (PARTITION BY practice ORDER BY month RANGE BETWEEN 1000000*3600*24*31*2 PRECEDING AND CURRENT ROW) AS denominator_in_window,
    COUNT(month) OVER (PARTITION BY practice ORDER BY month RANGE BETWEEN 1000000*3600*24*31*2 PRECEDING AND CURRENT ROW) AS window_size
  FROM (
    SELECT
    *,
      num.numerator AS numerator,
      denom.denominator AS denominator,
      denom.practice AS practice,
      denom.month AS month
    FROM (
      SELECT month, practice, {numerator_columns}
      FROM
        {numerator_from}
      WHERE
        {numerator_where}
      GROUP BY
        practice,
        month) num
    OUTER JOIN EACH (
      SELECT month, practice, {denominator_columns}
      FROM
        {denominator_from}
      WHERE
        {denominator_where}
      GROUP BY
        practice,
        month) denom
    ON
      (num.practice=denom.practice
        AND num.month=denom.month)) ratios
    INNER JOIN (
      SELECT org_code, provider_purchaser AS ccg
      FROM [ebmdatalab:hscic.epraccur]
      WHERE
        prescribing_setting = 4
        AND (opendate < "20160901" OR opendate IS NULL)
        AND (closedate > "20160901" OR closedate IS NULL)
        ) practices
    ON practices.org_code=ratios.practice
    )
WHERE
  window_size = 3
