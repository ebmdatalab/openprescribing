-- Section 6 of Implementation Guide (p46)

update dmd_product
set product_type = 3
where dmdid in (select
  dmdid
from dmd_product
inner join dmd_amp
  on dmd_amp.apid = dmd_product.dmdid
inner join dmd_vmp
  on dmd_amp.vpid = dmd_vmp.vpid
where dmd_vmp.nm = dmd_amp.nm
and product_type = 2)
