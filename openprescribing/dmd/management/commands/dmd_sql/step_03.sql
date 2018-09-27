-- Section 6 of Implementation Guide (p45)

update dmd_product_temp
set sched_1 = true
where dmdid in (select
  dmd_product_temp.dmdid
from dmd_product_temp
inner join dmd_amp
  on dmd_amp.apid = dmd_product_temp.dmdid
inner join dmd_ampp
  on dmd_ampp.apid = dmd_amp.apid
inner join dmd_prescrib_info
  on dmd_ampp.appid = dmd_prescrib_info.appid
  and dmd_prescrib_info.sched_1 = 1
left outer join (select
  dmdid
from dmd_product_temp
inner join dmd_amp
  on dmd_amp.apid = dmd_product_temp.dmdid
inner join dmd_ampp
  on dmd_ampp.apid = dmd_amp.apid
inner join dmd_prescrib_info
  on dmd_ampp.appid = dmd_prescrib_info.appid
  and dmd_prescrib_info.sched_1 != 1) notschedule_1
  on dmd_product_temp.dmdid = notschedule_1.dmdid
where notschedule_1.dmdid is null)
