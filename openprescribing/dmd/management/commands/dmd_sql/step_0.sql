-- Section 6 of Implementation Guide
drop table if exists dmd_product;
create table dmd_product (
  dmdid bigint primary key,
  bnf_code text,
  vpid bigint,
  display_name text,
  ema text,
  pres_statcd integer,
  avail_restrictcd integer,
  product_type integer,
  non_availcd integer,
  concept_class integer,
  nurse_f boolean,
  dent_f boolean,
  prod_order_no text,
  sched_1 boolean,
  sched_2 boolean,
  padm boolean,
  fp10_mda boolean,
  acbs boolean,
  assort_flav boolean,
  catcd integer,
  tariff_category integer,
  flag_imported boolean,
  flag_broken_bulk boolean,
  flag_non_bioequivalence boolean,
  flag_special_containers boolean
  );
