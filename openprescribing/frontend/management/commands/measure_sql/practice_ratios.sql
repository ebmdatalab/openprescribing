 WITH practices_with_months AS (
 -- Return a row for every practice in every month, even where
 -- there is no denominator value
  SELECT prescribing.month AS month,
         practices.code AS practice_id,
         pcn_id,
         ccg_id,
         stp_id,
         regional_team_id
  FROM {hscic}.practices AS practices
  CROSS JOIN (
    SELECT month
    FROM {denominator_from}
    GROUP BY month
  ) prescribing
  INNER JOIN {hscic}.ccgs ON practices.ccg_id = ccgs.code
  WHERE
    practices.setting = 4 AND
    DATE(month) >= '{start_date}' AND
    DATE(month) <= '{end_date}'
),

denom AS (
  SELECT month, practice, {denominator_columns}
  FROM
    {denominator_from}
  WHERE
    DATE(month) >= '{start_date}' AND DATE(month) <= '{end_date}'
    AND
      {denominator_where}
  GROUP BY
    practice,
    month
),

num AS (
  SELECT month, practice, {numerator_columns}
  FROM
    {numerator_from}
  WHERE
    DATE(month) >= '{start_date}' AND DATE(month) <= '{end_date}'
    AND
      {numerator_where}
  GROUP BY
    practice,
    month
)

SELECT
  numerator,
  denominator,
  practice_id,
  pcn_id,
  pct_id,
  stp_id,
  regional_team_id,
  month,
  IF(IS_INF(calc_value) OR IS_NAN(calc_value), NULL, calc_value) AS calc_value
  {aliased_denominators}
  {aliased_numerators}
FROM (
  SELECT
    -- Compute ratios
    *,
    IEEE_DIVIDE(numerator, denominator) AS calc_value
    FROM (
      SELECT
        -- a missing numerator or denominator means zero items
        -- prescribed
        COALESCE(num.numerator, 0) AS numerator,
        COALESCE(denom.denominator, 0) AS denominator,
        practices_with_months.practice_id,
        practices_with_months.pcn_id,
        practices_with_months.ccg_id AS pct_id,
        practices_with_months.stp_id,
        practices_with_months.regional_team_id,
        DATE(practices_with_months.month) AS month
        {numerator_aliases}
        {denominator_aliases}

      FROM practices_with_months
      LEFT JOIN num
        ON practices_with_months.practice_id = num.practice
          AND practices_with_months.month = num.month
      LEFT JOIN denom
        ON practices_with_months.practice_id = denom.practice
          AND practices_with_months.month = denom.month
   )
)
