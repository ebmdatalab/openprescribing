-- This outer select is purely to alias the columns
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
    -- Compute ratios
    *,
    numerator / denominator AS calc_value,
    numerator_in_window / denominator_in_window AS smoothed_calc_value
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
        denom.practice AS practice_id,
        denom.month AS month,
        -- required by the windowing function, above
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
      -- only examine standard GP practices
      ON practices.setting = 4 AND practices.code=ratios.practice_id AND (practices.open_date < FORMAT_TIMESTAMP('%Y-%m-%d', ratios.month) OR practices.open_date IS NULL) AND (practices.close_date > FORMAT_TIMESTAMP('%Y-%m-%d', ratios.month) or practices.close_date IS NULL)
      )
      -- Currently commented out because we're not ready to smooth things yet
      -- WHERE window_size = 3
)
