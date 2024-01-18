-- This SQL is checked in to the git repo at measure_sql/dmd_objs_with_form_route.sql.
-- Do not make changes directly in BQ!  Instead, change the version in the repo and run
--
--     ./manage.py create_bq_measure_views
--
-- This SQL return all dm+d objects with BNF codes, and links each object against its
-- VMP's form_route.

WITH vmps AS (
  SELECT
    'vmp' AS obj_type,
    1 AS order_key,
    id AS vpid,
    id AS snomed_id,
    bnf_code,
    nm AS name,
    ontformroute.descr AS form_route
  FROM {project}.{dmd}.vmp
  INNER JOIN {project}.{dmd}.ont ON vmp.id = ont.vmp
  INNER JOIN {project}.{dmd}.ontformroute ON ont.form = ontformroute.cd
),

amps AS (
  -- Find all AMPs with BNF codes belonging to the VMPs
  SELECT
    'amp' AS obj_type,
    2 AS order_key,
    vmp AS vpid,
    id AS snomed_id,
    amp.bnf_code,
    amp.descr AS name,
    form_route
  FROM {project}.{dmd}.amp
  INNER JOIN vmps ON amp.vmp = vmps.vpid
  WHERE vmp in (SELECT vpid FROM vmps) AND amp.bnf_code IS NOT NULL
),

vmpps AS (
  -- Find all VMPPs with BNF codes belonging to the VMPs
  SELECT
    'vmpp' AS obj_type,
    3 AS order_key,
    vmp AS vpid,
    id AS snomed_id,
    vmpp.bnf_code,
    vmpp.nm AS name,
    form_route
  FROM {project}.{dmd}.vmpp
  INNER JOIN vmps ON vmpp.vmp = vmps.vpid
  WHERE vmp in (SELECT vpid FROM vmps) AND vmpp.bnf_code IS NOT NULL
),


ampps AS (
  -- Find all VMPPs with BNF codes belonging to the VMPPs
  SELECT
    'ampp' AS obj_type,
    4 AS order_key,
    vmpps.vpid AS vpid,
    id AS snomed_id,
    ampp.bnf_code,
    ampp.nm AS name,
    vmpps.form_route
  FROM {project}.{dmd}.ampp
  INNER JOIN vmpps ON ampp.vmpp = vmpps.snomed_id
  WHERE vmpp in (SELECT snomed_id FROM vmpps) AND ampp.bnf_code IS NOT NULL
),

all_objs AS (
  -- Bung them all together
  SELECT * FROM vmps
  UNION ALL
  SELECT * FROM amps
  UNION ALL
  SELECT * FROM vmpps
  UNION ALL
  SELECT * FROM ampps
)

-- Sort them by BNF code, and then by VMP -> AMP -> VMPP -> AMPP
SELECT
  obj_type,
  vpid,
  snomed_id,
  all_objs.bnf_code,
  all_objs.name AS dmd_name,
  presentation.name AS bnf_name,
  form_route
FROM all_objs
INNER JOIN {project}.{hscic}.presentation
  ON all_objs.bnf_code = presentation.bnf_code
ORDER BY bnf_code, order_key
