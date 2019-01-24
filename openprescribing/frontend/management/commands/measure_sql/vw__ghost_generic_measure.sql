WITH
  single_ppu_dt AS (
  -- skips anything in the DT with more than one PPU (e.g. different
  -- per-pill prices for 7 and 28 pill packs), as we can't distinguish
  -- these in the dispensing data
  SELECT
    DISTINCT date,
    product
  FROM
    {project}.{dmd}.tariffprice dt
  INNER JOIN
    {project}.{dmd}.vmpp vmpp
  ON
    dt.vmpp = vmpp.vppid
  GROUP BY
    product,
    date
  HAVING
    STDDEV(price_pence/qtyval) = 0
    OR STDDEV(price_pence/qtyval) IS NULL),
  dt_prices AS (
  -- median prices for things in the Drug Tariff and not with multiple PPUs.
  -- We use median prices because the DT prices for the reimbursement
  -- month are not necessarily the ones used for reimbursements
  SELECT
    DISTINCT dt.date,
    product.bnf_code,
    dt.median_price_per_unit
  FROM
    `{project}.{measures}.vw__median_price_per_unit` dt
  INNER JOIN
    `{project}.{dmd}.product` product
  ON
    product.bnf_code = dt.bnf_code
  INNER JOIN
    single_ppu_dt
  ON
    dt.date= single_ppu_dt.date
    AND single_ppu_dt.product = product.dmdid)
-- now calculate possible savings against the median price
SELECT
  dt.date AS month,
  practice,
  --dt.median_price_per_unit,
  --CASE
  --  WHEN rx.quantity > 0 THEN ROUND((rx.net_cost / rx.quantity), 4)
  --  ELSE 0
  --END AS price_per_unit,
  --rx.quantity,
  rx.bnf_code,
  net_cost,
  net_cost - (ROUND(dt.median_price_per_unit, 4) * rx.quantity) AS possible_savings
FROM
  dt_prices dt
JOIN
  {project}.{hscic}.normalised_prescribing_standard rx
ON
  rx.month = dt.date
  AND rx.bnf_code = dt.bnf_code
WHERE
  -- lantanaprost quantities are broken in data
  rx.bnf_code <> '1106000L0AAAAAA'
  -- trivial savings / costs are discounted in the measure definition
