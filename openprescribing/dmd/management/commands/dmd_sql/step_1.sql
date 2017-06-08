-- Section 6 of Implementation Guide
create index if not exists i_vpid on dmd_product(vpid);
create index if not exists i_bnf_code on dmd_product(bnf_code);
create index if not exists i_dmdid on dmd_product(dmdid);
