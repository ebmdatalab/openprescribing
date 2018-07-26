from gcutils.bigquery import build_schema


DMD_SCHEMA = build_schema(
    ('dmdid', 'STRING'),
    ('bnf_code', 'STRING'),
    ('vpid', 'STRING'),
    ('display_name', 'STRING'),
    ('ema', 'STRING'),
    ('pres_statcd', 'STRING'),
    ('avail_restrictcd', 'STRING'),
    ('product_type', 'STRING'),
    ('non_availcd', 'STRING'),
    ('concept_class', 'STRING'),
    ('nurse_f', 'STRING'),
    ('dent_f', 'STRING'),
    ('prod_order_no', 'STRING'),
    ('sched_1', 'STRING'),
    ('sched_2', 'STRING'),
    ('padm', 'STRING'),
    ('fp10_mda', 'STRING'),
    ('acbs', 'STRING'),
    ('assort_flav', 'STRING'),
    ('catcd', 'STRING'),
    ('tariff_category', 'STRING'),
    ('flag_imported', 'STRING'),
    ('flag_broken_bulk', 'STRING'),
    ('flag_non_bioequivalence', 'STRING'),
    ('flag_special_containers', 'BOOLEAN')

)

CCG_SCHEMA = build_schema(
    ('code', 'STRING'),
    ('name', 'STRING'),
    ('ons_code', 'STRING'),
    ('org_type', 'STRING'),
    ('open_date', 'TIMESTAMP'),
    ('close_date', 'TIMESTAMP'),
    ('address', 'STRING'),
    ('postcode', 'STRING'),
)

PRESCRIBING_SCHEMA = build_schema(
    ('sha', 'STRING'),
    ('pct', 'STRING'),
    ('practice', 'STRING'),
    ('bnf_code', 'STRING'),
    ('bnf_name', 'STRING'),
    ('items', 'INTEGER'),
    ('net_cost', 'FLOAT'),
    ('actual_cost', 'FLOAT'),
    ('quantity', 'INTEGER'),
    ('month', 'TIMESTAMP'),
)

PRESENTATION_SCHEMA = build_schema(
    ('bnf_code', 'STRING'),
    ('name', 'STRING'),
    ('is_generic', 'BOOLEAN'),
    ('active_quantity', 'FLOAT'),
    ('adq', 'FLOAT'),
    ('adq_unit', 'STRING'),
    ('percent_of_adq', 'FLOAT'),
)

PRACTICE_SCHEMA = build_schema(
    ('code', 'STRING'),
    ('name', 'STRING'),
    ('address1', 'STRING'),
    ('address2', 'STRING'),
    ('address3', 'STRING'),
    ('address4', 'STRING'),
    ('address5', 'STRING'),
    ('postcode', 'STRING'),
    ('location', 'STRING'),
    ('ccg_id', 'STRING'),
    ('setting', 'INTEGER'),
    ('close_date', 'STRING'),
    ('join_provider_date', 'STRING'),
    ('leave_provider_date', 'STRING'),
    ('open_date', 'STRING'),
    ('status_code', 'STRING'),
)

PRACTICE_STATISTICS_SCHEMA = build_schema(
    ('month', 'TIMESTAMP'),
    ('male_0_4', 'INTEGER'),
    ('female_0_4', 'INTEGER'),
    ('male_5_14', 'INTEGER'),
    ('male_15_24', 'INTEGER'),
    ('male_25_34', 'INTEGER'),
    ('male_35_44', 'INTEGER'),
    ('male_45_54', 'INTEGER'),
    ('male_55_64', 'INTEGER'),
    ('male_65_74', 'INTEGER'),
    ('male_75_plus', 'INTEGER'),
    ('female_5_14', 'INTEGER'),
    ('female_15_24', 'INTEGER'),
    ('female_25_34', 'INTEGER'),
    ('female_35_44', 'INTEGER'),
    ('female_45_54', 'INTEGER'),
    ('female_55_64', 'INTEGER'),
    ('female_65_74', 'INTEGER'),
    ('female_75_plus', 'INTEGER'),
    ('total_list_size', 'INTEGER'),
    ('astro_pu_cost', 'FLOAT'),
    ('astro_pu_items', 'FLOAT'),
    ('star_pu', 'STRING'),
    ('pct_id', 'STRING'),
    ('practice', 'STRING')
)

TARIFF_SCHEMA = build_schema(
    ('bnf_name', 'STRING'),
    ('bnf_code', 'STRING'),
    ('category', 'STRING'),
    ('date', 'DATE'),
)

BNF_SCHEMA = build_schema(
  ('chapter', 'STRING'),
  ('chapter_code', 'STRING'),
  ('section', 'STRING'),
  ('section_code', 'STRING'),
  ('para', 'STRING'),
  ('para_code', 'STRING'),
  ('subpara', 'STRING'),
  ('subpara_code', 'STRING'),
  ('chemical', 'STRING'),
  ('chemical_code', 'STRING'),
  ('product', 'STRING'),
  ('product_code', 'STRING'),
  ('presentation', 'STRING'),
  ('presentation_code', 'STRING'),
)

PPU_SAVING_SCHEMA = build_schema(
    ('date', 'TIMESTAMP'),
    ('bnf_code', 'STRING'),
    ('lowest_decile', 'FLOAT'),
    ('quantity', 'INTEGER'),
    ('price_per_unit', 'FLOAT'),
    ('possible_savings', 'FLOAT'),
    ('formulation_swap', 'STRING'),
    ('pct_id', 'STRING'),
    ('practice_id', 'STRING'),
)


def statistics_transform(row):
    """Transform a row from the frontend_practicestatistics table so it
    matches our statistics schema

    """
    row[0] = "%s 00:00:00" % row[0]  # BQ TIMESTAMP format
    return row


def presentation_transform(row):
    """Transform a row from the frontend_presentation table so it
    matches our statistics schema

    """
    if row[2] == 't':
        row[2] = 'true'
    else:
        row[2] = 'false'
    return row


def ccgs_transform(row):
    if row[4]:
        row[4] = "%s 00:00:00" % row[4]
    if row[5]:
        row[5] = "%s 00:00:00" % row[5]
    return row


def ppu_savings_transform(row):
    if row[0]:
        row[0] = "%s 00:00:00" % row[0]
    return row
