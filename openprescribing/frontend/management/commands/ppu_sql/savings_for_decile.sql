SELECT
  bnf.presentation,
  bnf.chemical,
  {{ select }}
  savings.generic_presentation AS generic_presentation,
  savings.category AS category,
  savings.avg_brand_count_per_practice AS avg_brand_count_per_practice,
  savings.deciles.lowest_decile AS lowest_decile,
  savings.quantity AS quantity,
  savings.price_per_unit AS price_per_unit,
  savings.possible_savings AS possible_savings
FROM (
  SELECT
      {{ inner_select }}
      generic_presentation,
      deciles.lowest_decile,
      AVG(brand_count) AS avg_brand_count_per_practice,
      MAX(category) AS category,
      SUM(quantity) AS quantity,
      AVG(price_per_unit) AS price_per_unit,
      SUM(possible_savings) AS possible_savings
    FROM (
    -- Always select per-practice initially, so we can apply "diode"
    -- to exclude negative cost savings
    SELECT
      presentations.practice,
      presentations.pct,
      presentations.generic_presentation AS generic_presentation,
      COUNT(DISTINCT bnf_code) AS brand_count,
      MAX(presentations.category) AS category,
      deciles.lowest_decile,
      SUM(presentations.quantity) AS quantity,
      SUM(presentations.net_cost)/SUM(presentations.quantity) AS price_per_unit,
      GREATEST((SUM(presentations.net_cost) - (SUM(presentations.quantity) * deciles.lowest_decile)), 0) AS possible_savings -- the "diode"
    FROM (
      SELECT
        *
      FROM (
          -- Create table for joining individual data
        SELECT
          practice,
          pct,
          p.bnf_code AS bnf_code,
          t.category AS category,
          IF(
            LENGTH(RTRIM(p.bnf_code)) = 15 -- excludes devices etc
              AND (
                SUBSTR(p.bnf_code, 14, 15) != 'A0' -- excludes things without generic equivalents
                OR SUBSTR(p.bnf_code, 1, 9) == '0601060U0' OR SUBSTR(p.bnf_code, 1, 9) == '0601060D0'), -- unless they're one of our two exceptions -- see issue #1
            CONCAT(SUBSTR(p.bnf_code, 1, 9), 'AA', SUBSTR(p.bnf_code, 14, 2), SUBSTR(p.bnf_code, 14, 2)),
            NULL) AS generic_presentation,
          net_cost,
          quantity
        FROM
          {{ prescribing_table }} AS p
        LEFT JOIN {hscic}.tariff t
          ON p.bnf_code = t.bnf_code
        LEFT JOIN {hscic}.practices practices
          ON p.practice = practices.code
        WHERE
          practices.setting = 4 AND
          month = TIMESTAMP("{{ month }}")
          {{ restricting_condition }}
          ) ) presentations
    JOIN (
        -- Calculate the top decile of price per dose for each generic presentation
      SELECT
        generic_presentation,
        MAX(lowest_decile) AS lowest_decile
      FROM (
        SELECT
          generic_presentation,
          PERCENTILE_CONT(0.1) OVER (PARTITION BY generic_presentation ORDER BY price_per_unit ASC) AS lowest_decile
        FROM (
            -- Calculate price per dose for each presentation, normalising the codes across brands/generics
          SELECT
            IF(
              LENGTH(RTRIM(p.bnf_code)) = 15 -- excludes devices etc
                AND (
                  SUBSTR(bnf_code, 14, 15) != 'A0' -- excludes things without generic equivalents
                  OR SUBSTR(bnf_code, 1, 9) == '0601060U0' OR SUBSTR(bnf_code, 1, 9) == '0601060D0'), -- unless they're one of our two exceptions -- see issue #1
              CONCAT(SUBSTR(bnf_code, 1, 9), 'AA', SUBSTR(bnf_code, 14, 2), SUBSTR(bnf_code, 14, 2)),
              NULL) AS generic_presentation,
            AVG(net_cost/quantity) AS price_per_unit
          FROM
            {{ prescribing_table }} AS p
          LEFT JOIN {hscic}.practices practices
            ON p.practice = practices.code
          WHERE
            practices.setting = 4 AND
            month = TIMESTAMP("{{ month }}")
            {{ restricting_condition }}
          GROUP BY practice, generic_presentation)
          )
      WHERE generic_presentation IS NOT NULL
      GROUP BY
        generic_presentation) deciles
    ON
      deciles.generic_presentation = presentations.generic_presentation
    GROUP BY
      presentations.practice,
      presentations.pct,
      generic_presentation,
      deciles.lowest_decile
  )

  GROUP BY
    generic_presentation,
    deciles.lowest_decile,
    {{ group_by }}
    {{ order_by }}
) savings
LEFT JOIN
  (SELECT
    *
  FROM {hscic}.bnf, (
    SELECT
      'Glucose Blood Testing Reagents' AS presentation,
      'Glucose Blood Testing Reagents' AS chemical,
      '0601060D0AAA0A0' AS presentation_code),
    (
    SELECT
      'Urine Testing Reagents' AS presentation,
      'Urine Testing Reagents' AS chemical,
      '0601060U0AAA0A0' AS presentation_code)) bnf
ON
  bnf.presentation_code = savings.generic_presentation
WHERE possible_savings >= {{ min_saving }}
