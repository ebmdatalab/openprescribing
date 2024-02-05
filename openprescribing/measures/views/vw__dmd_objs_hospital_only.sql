-- This SQL finds all AMPs which are hospital only, and all VMPs which have at
-- least one hospital only AMP.

WITH amps AS (
  -- Find all hospital only AMPs
  SELECT
    'amp' AS obj_type,
    2 AS order_key,
    id AS snomed_id,
    vmp AS vpid,
    bnf_code,
    descr AS name
  FROM {project}.{dmd}.amp
  WHERE avail_restrict = 8 -- hospital only
),

vmps AS (
   -- Find all VMPs corresponding to these AMPs
  SELECT
    'vmp' AS obj_type,
    1 AS order_key,
    vmp.id AS snomed_id,
    vmp.id AS vpid,
    vmp.bnf_code,
    vmp.nm AS name
  FROM {project}.{dmd}.vmp
  INNER JOIN amps ON vmp.id = amps.vpid
),

all_objs AS (
  -- Bung them all together
  SELECT * FROM amps
  UNION ALL
  SELECT * FROM vmps
)

-- Sort them by BNF code, and then by VMP -> AMP
SELECT
  obj_type,
  snomed_id,
  all_objs.bnf_code,
  all_objs.name AS dmd_name,
  presentation.name AS bnf_name
FROM all_objs
INNER JOIN {project}.{hscic}.presentation
  ON all_objs.bnf_code = presentation.bnf_code
ORDER BY bnf_code, order_key
