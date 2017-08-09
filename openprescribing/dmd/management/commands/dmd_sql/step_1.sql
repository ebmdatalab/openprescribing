-- Section 6 of Implementation Guide
create index if not exists i_vpid on dmd_product_temp(vpid);
create index if not exists i_bnf_code on dmd_product_temp(bnf_code);
create index if not exists i_dmdid on dmd_product_temp(dmdid);
create index if not exists i_name on dmd_product_temp(name);
