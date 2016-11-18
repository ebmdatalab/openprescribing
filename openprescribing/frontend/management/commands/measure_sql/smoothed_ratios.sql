SELECT
  numerator,
  denominator,
  practice_id,
  ccg_id AS pct_id,
  DATE(month) AS month,
  calc_value,
  smoothed_calc_value
  {aliased_denominators}
  {aliased_numerators}
FROM (
  SELECT
    *,
    numerator / denominator AS calc_value,
    numerator_in_window / denominator_in_window AS smoothed_calc_value
  FROM (
    SELECT
      *,
      SUM(numerator) OVER (PARTITION BY practice_id ORDER BY month_secs RANGE BETWEEN 5356800 PRECEDING AND CURRENT ROW) AS numerator_in_window,
      SUM(denominator) OVER (PARTITION BY practice_id ORDER BY month_secs RANGE BETWEEN 5356800 PRECEDING AND CURRENT ROW) AS denominator_in_window,
      COUNT(month) OVER (PARTITION BY practice_id ORDER BY month_secs RANGE BETWEEN 5356800 PRECEDING AND CURRENT ROW) AS window_size
    FROM (
      SELECT
        COALESCE(num.numerator, 0) AS numerator,
        COALESCE(denom.denominator, 0) AS denominator,
        denom.practice AS practice_id,
        denom.month AS month,
        UNIX_SECONDS(denom.month) AS month_secs
        {numerator_aliases}
        {denominator_aliases}
      FROM (
        SELECT month, practice, {numerator_columns}
        FROM
          {numerator_from}
        WHERE
          {numerator_where}
        GROUP BY
          practice,
          month) num
      RIGHT JOIN (
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
      INNER JOIN
        ebmdatalab.hscic.practices
      ON practices.setting = 4 AND practices.code=ratios.practice_id AND (practices.open_date < FORMAT_TIMESTAMP('%Y-%m-%d', ratios.month) OR practices.open_date IS NULL) AND (practices.close_date > FORMAT_TIMESTAMP('%Y-%m-%d', ratios.month) or practices.close_date IS NULL)
      )
      --- WHERE window_size = 3
)
