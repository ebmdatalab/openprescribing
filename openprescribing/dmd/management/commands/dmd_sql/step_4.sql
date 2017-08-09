-- Section 6 of Implementation Guide (p46)

update dmd_product_temp
set product_type = 3
where dmdid in (select
  dmdid
from dmd_product_temp
inner join dmd_amp
  on dmd_amp.apid = dmd_product_temp.dmdid
inner join dmd_vmp
  on dmd_amp.vpid = dmd_vmp.vpid
where dmd_vmp.nm = dmd_amp.nm
and product_type = 2)
