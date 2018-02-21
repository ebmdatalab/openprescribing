-- This outer select is purely to alias the columns
SELECT
  numerator,
  denominator,
  practice_id,
  ccg_id AS pct_id,
  DATE(month) AS month,
  IF(IS_INF(calc_value) OR IS_NAN(calc_value), NULL, calc_value) AS calc_value
  {aliased_denominators}
  {aliased_numerators}
FROM (
  SELECT
    -- Compute ratios
    *,
    IEEE_DIVIDE(numerator, denominator) AS calc_value,
    IEEE_DIVIDE(numerator_in_window, denominator_in_window) AS smoothed_calc_value
  FROM (
    SELECT
      -- Calculate sums over a rolling three month window for smoothed
      -- averages. The number 5356800 is the number of seconds in a 32
      -- * 3 days; more than three months, but as our data is only
      -- monthly, this is a safe way to select the window. Note that
      -- we filter to windows of size three later in ths query
      *,
      SUM(numerator) OVER (PARTITION BY practice_id ORDER BY month_secs RANGE BETWEEN 5356800 PRECEDING AND CURRENT ROW) AS numerator_in_window,
      SUM(denominator) OVER (PARTITION BY practice_id ORDER BY month_secs RANGE BETWEEN 5356800 PRECEDING AND CURRENT ROW) AS denominator_in_window,
      COUNT(month) OVER (PARTITION BY practice_id ORDER BY month_secs RANGE BETWEEN 5356800 PRECEDING AND CURRENT ROW) AS window_size
    FROM (
      SELECT
        -- a missing numerator or denominator means zero items
        -- prescribed
        COALESCE(num.numerator, 0) AS numerator,
        COALESCE(denom.denominator, 0) AS denominator,
        practices_with_months.practice_id,
        practices_with_months.ccg_id AS ccg_id,
        practices_with_months.month,
        -- required by the windowing function, above
        UNIX_SECONDS(denom.month) AS month_secs
        {numerator_aliases}
        {denominator_aliases}
      FROM (
        SELECT month, practice, {numerator_columns}
        FROM
          {numerator_from}
        WHERE
          DATE(month) >= '{start_date}' AND DATE(month) <= '{end_date}'
          AND
            {numerator_where}
        GROUP BY
          practice,
          month) num
      RIGHT JOIN (
        SELECT month, practice, {denominator_columns}
        FROM
          {denominator_from}
        WHERE
          DATE(month) >= '{start_date}' AND DATE(month) <= '{end_date}'
          AND
            {denominator_where}
        GROUP BY
          practice,
          month) denom
      ON
        (num.practice=denom.practice
          AND num.month=denom.month)
      RIGHT JOIN
         (
         -- Return a row for every practice in every month, even where
         -- there is no denominator value
          SELECT prescribing.month AS month,
                 practices.code AS practice_id,
                 ccg_id
            FROM {hscic}.practices AS practices
            CROSS JOIN (
              SELECT month
              FROM {denominator_from}
              GROUP BY month) prescribing
            WHERE
              practices.setting = 4 AND
              DATE(month) >= '{start_date}' AND
              DATE(month) <= '{end_date}') practices_with_months
      ON practices_with_months.practice_id = denom.practice
       AND practices_with_months.month = denom.month
      -- Currently commented out because we're not ready to smooth things yet
      -- WHERE window_size = 3
      )
   )
)
