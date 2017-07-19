SELECT
  month,
  FORMAT("%.2f", ROUND(SUM(actual_cost), 2)) AS actual_cost,
  SUM(items) AS items,
  SUM(quantity) AS quantity
FROM
  `hscic.prescribing`
WHERE
  (bnf_code='0403030E0AAAAAA')
  AND pct='10Q'
  AND {{ date_condition }}
GROUP BY
  month
ORDER BY
  month ASC
