SELECT
  month,
  SUM(items) AS items,
  FORMAT("%.2f", ROUND(SUM(actual_cost), 2)) AS actual_cost,
  SUM(quantity) AS quantity
FROM
  `{hscic}.normalised_prescribing_standard`
WHERE
  (bnf_code LIKE '0212000B0%' OR bnf_code LIKE '0212000B0%'
  OR bnf_code LIKE '0212000C0%' OR bnf_code LIKE '0212000M0%'
  OR bnf_code LIKE '0212000X0%' OR bnf_code LIKE '0212000Y0%')
  AND practice='C85020'
  AND {{ date_condition }}

GROUP BY
  month
ORDER BY
  month ASC
