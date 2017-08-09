-- ACBS flag
-- Section 6 of Implementation Guide (p50)

update dmd_product_temp
set acbs = true
where dmdid in (
  select dmdid
  from dmd_product_temp
  inner join dmd_amp
    on dmd_amp.vpid = dmdid
    or dmd_amp.apid = dmdid
  inner join dmd_ampp
    on dmd_ampp.apid = dmd_amp.apid
  inner join dmd_prescrib_info
    on dmd_ampp.appid = dmd_prescrib_info.appid
  where dmd_prescrib_info.acbs = 1);
