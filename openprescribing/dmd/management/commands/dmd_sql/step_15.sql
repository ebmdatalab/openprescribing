-- whether a given VMP  is in the Drug Tariff
-- Based on query on p78 of Implementation Guide
update dmd_product_temp
set tariff_category = subquery.pay_catcd2
from (
  SELECT
    dmd_product_temp.*, dmd_dtinfo.pay_catcd AS pay_catcd2
  FROM
    dmd_product_temp
  INNER JOIN
    dmd_vmpp
  ON
    dmd_vmpp.vpid = dmd_product_temp.vpid
  INNER JOIN
    dmd_dtinfo
  ON
    dmd_dtinfo.vppid = dmd_vmpp.vppid) AS subquery
WHERE dmd_product_temp.dmdid = subquery.dmdid
