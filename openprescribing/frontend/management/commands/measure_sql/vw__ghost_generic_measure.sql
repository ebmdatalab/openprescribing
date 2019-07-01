-- This SQL is checked in to the git repo at measure_sql/vw__ghost_generic_measure.sql.
-- Do not make changes directly in BQ!  Instead, change the version in the repo and run
--
--     ./manage.py create_bq_measure_views

WITH
  vmps_with_one_ppu AS (
      SELECT
        DISTINCT tp.date,
        vmp.bnf_code
      FROM {project}.{dmd}.vmp
      INNER JOIN {project}.{dmd}.vmpp ON vmp.id = vmpp.vmp
      INNER JOIN {project}.{dmd}.tariffprice tp ON vmpp.id = tp.vmpp
      GROUP BY
        tp.date,
        vmp.bnf_code
      HAVING
        STDDEV(tp.price_pence / vmpp.qtyval) = 0
        OR STDDEV(tp.price_pence / vmpp.qtyval) IS NULL
  ),

  dt_prices AS (
    -- median prices for things in the Drug Tariff and not with multiple PPUs.
    -- We use median prices because the DT prices for the reimbursement
    -- month are not necessarily the ones used for reimbursements
    SELECT
      DISTINCT vw.date,
      vw.bnf_code,
      vw.median_price_per_unit
    FROM
      {project}.{measures}.vw__median_price_per_unit vw

    INNER JOIN
      {project}.{dmd}.vmp
    ON
      vmp.bnf_code = vw.bnf_code

    INNER JOIN
      vmps_with_one_ppu
    ON
      vw.bnf_code = vmps_with_one_ppu.bnf_code
      AND vw.date = vmps_with_one_ppu.date
  )

-- now calculate possible savings against the median price
SELECT
  dt.date AS month,
  practice,
  rx.bnf_code,
  net_cost,
  net_cost - (ROUND(dt.median_price_per_unit, 4) * rx.quantity) AS possible_savings
FROM
  dt_prices dt
INNER JOIN
  {project}.{hscic}.normalised_prescribing_standard rx
ON
  rx.month = dt.date
  AND rx.bnf_code = dt.bnf_code
WHERE
-- These can be prescribed fractionally, but BSA round quantity down,
-- making quantity unreliable. See #1764
  rx.bnf_code <> '1106000L0AAAAAA' -- latanoprost
AND
  rx.bnf_code <> '1308010Z0AAABAB' -- Ingenol Mebutate_Gel

-- trivial savings / costs are discounted in the measure definition
