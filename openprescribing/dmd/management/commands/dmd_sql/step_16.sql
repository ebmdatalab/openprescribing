-- Various other useful flags (not in Implementation Guide)

update dmd_product
set flag_broken_bulk = true
where dmdid in (select
  dmd_product.dmdid
from dmd_product
inner join dmd_amp
  on dmd_amp.apid = dmd_product.dmdid
inner join dmd_ampp
  on dmd_ampp.apid = dmd_amp.apid
inner join dmd_reimb_info
  on dmd_ampp.appid = dmd_reimb_info.appid
  and dmd_reimb_info.bb = 1);

update dmd_product
set flag_imported = true
where dmdid in (select
  dmd_product.dmdid
from dmd_product
where avail_restrictcd = 4);


update dmd_product
set flag_non_bioequivalence = true
where dmdid in (select dmdid
from dmd_product
inner join dmd_vmpp
  on dmd_vmpp.vpid = dmdid
inner join dmd_vmp
  on dmd_vmpp.vpid = dmd_vmp.vpid
where dmd_vmp.pres_statcd = 6);


update dmd_product
set flag_special_containers = true
where dmdid in (
select dmdid from dmd_product
inner join dmd_amp
  on dmd_amp.apid = dmdid
  or dmd_amp.vpid = dmdid
inner join dmd_ampp
  on dmd_ampp.apid = dmd_amp.apid
inner join dmd_reimb_info
  on dmd_ampp.appid = dmd_reimb_info.appid
  and spec_contcd = 1);
