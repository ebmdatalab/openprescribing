# icsdose denominator

SELECT "v1" as v, sum(items) AS items
FROM hscic.prescribing_v1
WHERE practice != '-' AND month = '2019-12-01' AND (
  bnf_code LIKE "0302000C0%" OR
  bnf_code LIKE "0302000K0%" OR
  bnf_code LIKE "0302000N0%" OR
  bnf_code LIKE "0302000R0%" OR
  bnf_code LIKE "0302000U0%" OR
  bnf_code LIKE "0302000V0%" OR
  bnf_code LIKE "0301011AB%"
) AND NOT (
  bnf_code LIKE "0302000N0%AV" OR
  bnf_code LIKE "0302000N0%AW"
)

UNION ALL

SELECT "v2" as v, sum(items) AS items
FROM hscic.prescribing_v2
WHERE practice != '-' AND month = '2019-12-01' AND (
  bnf_code LIKE "0302000C0%" OR
  bnf_code LIKE "0302000K0%" OR
  bnf_code LIKE "0302000N0%" OR
  bnf_code LIKE "0302000R0%" OR
  bnf_code LIKE "0302000U0%" OR
  bnf_code LIKE "0302000V0%" OR
  bnf_code LIKE "0301011AB%"
) AND NOT (
  bnf_code LIKE "0302000N0%AV" OR
  bnf_code LIKE "0302000N0%AW"
)

ORDER BY v

-----

# icsdose numerator

SELECT "v1" as v, sum(items) AS items
FROM hscic.prescribing_v1
WHERE practice != '-' AND month = '2019-12-01' AND (
  bnf_code LIKE "0302000C0%AC" OR
  bnf_code LIKE "0302000C0%AU" OR
  bnf_code LIKE "0302000C0%BK" OR
  bnf_code LIKE "0302000C0%BW" OR
  bnf_code LIKE "0302000C0%BZ" OR
  bnf_code LIKE "0302000C0%CA" OR
  bnf_code LIKE "0302000K0%AH" OR
  bnf_code LIKE "0302000K0%AY" OR
  bnf_code LIKE "0302000K0%AU" OR
  bnf_code LIKE "0302000N0%AF" OR
  bnf_code LIKE "0302000N0%AP" OR
  bnf_code LIKE "0302000N0%AU" OR
  bnf_code LIKE "0302000N0%AZ" OR
  bnf_code LIKE "0302000N0%BC" OR
  bnf_code LIKE "0302000N0%BG" OR
  bnf_code LIKE "0302000N0%BK" OR
  bnf_code LIKE "0302000U0%AB" OR
  bnf_code LIKE "0302000U0%AC" OR
  bnf_code LIKE "0302000V0%AA"
)

UNION ALL

SELECT "v2" as v, sum(items) AS items
FROM hscic.prescribing_v2
WHERE practice != '-' AND month = '2019-12-01' AND (
  bnf_code LIKE "0302000C0%AC" OR
  bnf_code LIKE "0302000C0%AU" OR
  bnf_code LIKE "0302000C0%BK" OR
  bnf_code LIKE "0302000C0%BW" OR
  bnf_code LIKE "0302000C0%BZ" OR
  bnf_code LIKE "0302000C0%CA" OR
  bnf_code LIKE "0302000K0%AH" OR
  bnf_code LIKE "0302000K0%AY" OR
  bnf_code LIKE "0302000K0%AU" OR
  bnf_code LIKE "0302000N0%AF" OR
  bnf_code LIKE "0302000N0%AP" OR
  bnf_code LIKE "0302000N0%AU" OR
  bnf_code LIKE "0302000N0%AZ" OR
  bnf_code LIKE "0302000N0%BC" OR
  bnf_code LIKE "0302000N0%BD" OR
  bnf_code LIKE "0302000N0%BG" OR
  bnf_code LIKE "0302000N0%BK" OR
  bnf_code LIKE "0302000U0%AB" OR
  bnf_code LIKE "0302000V0%AA"
)

ORDER BY v

-----

WITH v1 AS (
  SELECT bnf_code AS v1_bnf_code, SUM(items) AS v1_items
  FROM hscic.prescribing_v1
  WHERE month = '2019-12-01' AND (
    bnf_code LIKE '0401%' AND
    bnf_code NOT LIKE '0401010AC%' AND
    bnf_code NOT LIKE '0401010AD%' AND
    bnf_code NOT LIKE '0401020K0%AD' AND
    bnf_code NOT LIKE '0401020K0%AE' AND
    bnf_code NOT LIKE '0401020K0%BQ'
  )
  GROUP BY bnf_code
),

v1_full AS (
  SELECT v1_bnf_code, presentation AS v1_bnf_name, v1_items
  FROM v1 LEFT OUTER JOIN hscic.bnf ON v1_bnf_code = bnf.presentation_code
),

v2 AS (
  SELECT bnf_code AS v2_bnf_code, SUM(items) AS v2_items
  FROM hscic.prescribing_v2
  WHERE month = '2019-12-01' AND (
    bnf_code LIKE '0401%' AND
    bnf_code NOT LIKE '0401010AC%' AND
    bnf_code NOT LIKE '0401010AD%' AND
    bnf_code NOT LIKE '0401020K0%AD' AND
    bnf_code NOT LIKE '0401020K0%AE' AND
    bnf_code NOT LIKE '0401020K0%BQ'
  )
  GROUP BY bnf_code
),

v2_full AS (
  SELECT v2_bnf_code, presentation AS v2_bnf_name, v2_items
  FROM v2 LEFT OUTER JOIN hscic.bnf ON v2_bnf_code = bnf.presentation_code
)

SELECT
  COALESCE(v1_bnf_code, v2_bnf_code) AS bnf_code,
  COALESCE(v1_bnf_name, v2_bnf_name) AS bnf_name,
  COALESCE(v1_items, 0) AS v1_items,
  COALESCE(v2_items, 0) AS v2_items
FROM v1_full FULL OUTER JOIN v2_full ON v1_bnf_code = v2_bnf_code
WHERE COALESCE(v1_items, 0) != COALESCE(v2_items, 0)

