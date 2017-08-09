-- whether an item can be prescribed in instalments
-- on a FP10 MDA form
-- Section 6 of Implementation Guide (p51)

update dmd_product_temp
set fp10_mda = true
where dmdid in (
  select dmdid
  from dmd_product_temp
  inner join dmd_amp
    on dmd_amp.vpid = dmdid
    or dmd_amp.apid = dmdid
  inner join dmd_ampp
    on dmd_amp.apid = dmd_ampp.apid
  inner join dmd_prescrib_info
    on dmd_prescrib_info.appid = dmd_ampp.appid
  where dmd_prescrib_info.fp10_mda = 1)
