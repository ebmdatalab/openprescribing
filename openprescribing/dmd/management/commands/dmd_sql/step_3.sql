-- Section 6 of Implementation Guide (p45)

update dmd_product
set sched_1 = true
where dmdid in (select
  dmd_product.dmdid
from dmd_product
inner join dmd_amp
  on dmd_amp.apid = dmd_product.dmdid
inner join dmd_ampp
  on dmd_ampp.apid = dmd_amp.apid
inner join dmd_prescrib_info
  on dmd_ampp.appid = dmd_prescrib_info.appid
  and dmd_prescrib_info.sched_1 = 1
left outer join (select
  dmdid
from dmd_product
inner join dmd_amp
  on dmd_amp.apid = dmd_product.dmdid
inner join dmd_ampp
  on dmd_ampp.apid = dmd_amp.apid
inner join dmd_prescrib_info
  on dmd_ampp.appid = dmd_prescrib_info.appid
  and dmd_prescrib_info.sched_1 != 1) notschedule_1
  on dmd_product.dmdid = notschedule_1.dmdid
where notschedule_1.dmdid is null)
