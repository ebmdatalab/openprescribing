--
-- PostgreSQL schema dump for DMD tables This is currently only used
-- by the `sample_data` command in the `frontend` app, for table
-- setup.  If/when DMD structure changes, this file should be changed
-- as well.
--
-- Created with pg_dump --schema-only --no-privileges --no-owner
-- --clean --if-exists --table="dmd_*" prescribing; edited to remove
-- database settings and to add `CASCADE`.
--
--
-- Dumped from database version 9.6.1
-- Dumped by pg_dump version 9.6.1


ALTER TABLE IF EXISTS ONLY public.dmd_tariffprice DROP CONSTRAINT IF EXISTS dmd_tariffprice_product_id_39bb1b2e_fk_dmd_product_dmdid CASCADE;
DROP INDEX IF EXISTS public.i_vpid CASCADE;
DROP INDEX IF EXISTS public.i_name CASCADE;
DROP INDEX IF EXISTS public.i_dmdid CASCADE;
DROP INDEX IF EXISTS public.i_dmd_vpi_vpid CASCADE;
DROP INDEX IF EXISTS public.i_dmd_vmpp_vpid CASCADE;
DROP INDEX IF EXISTS public.i_dmd_reimb_info_appid CASCADE;
DROP INDEX IF EXISTS public.i_dmd_price_info_appid CASCADE;
DROP INDEX IF EXISTS public.i_dmd_prescrib_info_appid CASCADE;
DROP INDEX IF EXISTS public.i_dmd_pack_info_appid CASCADE;
DROP INDEX IF EXISTS public.i_dmd_ont_vpid CASCADE;
DROP INDEX IF EXISTS public.i_dmd_lic_route_apid CASCADE;
DROP INDEX IF EXISTS public.i_dmd_dtinfo_vppid CASCADE;
DROP INDEX IF EXISTS public.i_dmd_droute_vpid CASCADE;
DROP INDEX IF EXISTS public.i_dmd_dform_vpid CASCADE;
DROP INDEX IF EXISTS public.i_dmd_control_info_vpid CASCADE;
DROP INDEX IF EXISTS public.i_dmd_ap_ing_apid CASCADE;
DROP INDEX IF EXISTS public.i_dmd_ap_info_apid CASCADE;
DROP INDEX IF EXISTS public.i_dmd_ampp_vppid CASCADE;
DROP INDEX IF EXISTS public.i_dmd_ampp_apid CASCADE;
DROP INDEX IF EXISTS public.i_dmd_amp_vpid CASCADE;
DROP INDEX IF EXISTS public.i_bnf_code CASCADE;
DROP INDEX IF EXISTS public.dmd_tariffprice_9bea82de CASCADE;
DROP INDEX IF EXISTS public.dmd_tariffprice_5fc73231 CASCADE;
DROP INDEX IF EXISTS public.dmd_tariffprice_53e32515 CASCADE;
DROP INDEX IF EXISTS public.dmd_tariffprice_26eb061f CASCADE;
DROP INDEX IF EXISTS public.dmd_ncsoconcession_5fc73231 CASCADE;
DROP INDEX IF EXISTS public.dmd_ncsoconcession_26eb061f CASCADE;
ALTER TABLE IF EXISTS ONLY public.dmd_vmpp DROP CONSTRAINT IF EXISTS dmd_vmpp_pkey CASCADE;
ALTER TABLE IF EXISTS ONLY public.dmd_vmp DROP CONSTRAINT IF EXISTS dmd_vmp_pkey CASCADE;
ALTER TABLE IF EXISTS ONLY public.dmd_tariffprice DROP CONSTRAINT IF EXISTS dmd_tariffprice_pkey CASCADE;
ALTER TABLE IF EXISTS ONLY public.dmd_tariffprice DROP CONSTRAINT IF EXISTS dmd_tariffprice_date_a7f529c9_uniq CASCADE;
ALTER TABLE IF EXISTS ONLY public.dmd_product_temp DROP CONSTRAINT IF EXISTS dmd_product_temp_pkey1 CASCADE;
ALTER TABLE IF EXISTS ONLY public.dmd_product DROP CONSTRAINT IF EXISTS dmd_product_temp_pkey CASCADE;
ALTER TABLE IF EXISTS ONLY public.dmd_ncsoconcession DROP CONSTRAINT IF EXISTS dmd_ncsoconcession_pkey CASCADE;
ALTER TABLE IF EXISTS ONLY public.dmd_ncsoconcession DROP CONSTRAINT IF EXISTS dmd_ncsoconcession_date_a1a20bea_uniq CASCADE;
ALTER TABLE IF EXISTS ONLY public.dmd_ampp DROP CONSTRAINT IF EXISTS dmd_ampp_pkey CASCADE;
ALTER TABLE IF EXISTS ONLY public.dmd_amp DROP CONSTRAINT IF EXISTS dmd_amp_pkey CASCADE;
ALTER TABLE IF EXISTS public.dmd_tariffprice ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.dmd_ncsoconcession ALTER COLUMN id DROP DEFAULT;
DROP TABLE IF EXISTS public.dmd_vtm CASCADE;
DROP TABLE IF EXISTS public.dmd_vpi CASCADE;
DROP TABLE IF EXISTS public.dmd_vmpp CASCADE;
DROP TABLE IF EXISTS public.dmd_vmp CASCADE;
DROP SEQUENCE IF EXISTS public.dmd_tariffprice_id_seq CASCADE;
DROP TABLE IF EXISTS public.dmd_tariffprice CASCADE;
DROP TABLE IF EXISTS public.dmd_reimb_info CASCADE;
DROP TABLE IF EXISTS public.dmd_product_temp CASCADE;
DROP TABLE IF EXISTS public.dmd_product CASCADE;
DROP TABLE IF EXISTS public.dmd_price_info CASCADE;
DROP TABLE IF EXISTS public.dmd_prescrib_info CASCADE;
DROP TABLE IF EXISTS public.dmd_pack_info CASCADE;
DROP TABLE IF EXISTS public.dmd_ont CASCADE;
DROP SEQUENCE IF EXISTS public.dmd_ncsoconcession_id_seq CASCADE;
DROP TABLE IF EXISTS public.dmd_ncsoconcession CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_virtual_product_pres_status CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_virtual_product_non_avail CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_unit_of_measure CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_supplier CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_spec_cont CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_route CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_reimbursement_status CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_price_basis CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_ont_form_route CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_namechange_reason CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_licensing_authority_change_reason CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_licensing_authority CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_legal_category CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_form CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_flavour CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_dt_payment_category CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_dnd CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_discontinued_ind CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_df_indicator CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_control_drug_category CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_combination_prod_ind CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_combination_pack_ind CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_colour CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_basis_of_strnth CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_basis_of_name CASCADE;
DROP TABLE IF EXISTS public.dmd_lookup_availability_restriction CASCADE;
DROP TABLE IF EXISTS public.dmd_lic_route CASCADE;
DROP TABLE IF EXISTS public.dmd_ing CASCADE;
DROP TABLE IF EXISTS public.dmd_gtin CASCADE;
DROP TABLE IF EXISTS public.dmd_dtinfo CASCADE;
DROP TABLE IF EXISTS public.dmd_droute CASCADE;
DROP TABLE IF EXISTS public.dmd_dform CASCADE;
DROP TABLE IF EXISTS public.dmd_control_info CASCADE;
DROP TABLE IF EXISTS public.dmd_ccontent CASCADE;
DROP TABLE IF EXISTS public.dmd_ap_ing CASCADE;
DROP TABLE IF EXISTS public.dmd_ap_info CASCADE;
DROP TABLE IF EXISTS public.dmd_ampp CASCADE;
DROP TABLE IF EXISTS public.dmd_amp CASCADE;
SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: dmd_amp; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_amp (
    apid bigint NOT NULL,
    invalid bigint,
    vpid bigint,
    nm text,
    abbrevnm text,
    "desc" text,
    nmdt date,
    nm_prev text,
    suppcd bigint,
    lic_authcd bigint,
    lic_auth_prevcd bigint,
    lic_authchangecd bigint,
    lic_authchangedt date,
    combprodcd bigint,
    flavourcd bigint,
    ema bigint,
    parallel_import bigint,
    avail_restrictcd bigint
);


--
-- Name: dmd_ampp; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_ampp (
    appid bigint NOT NULL,
    invalid bigint,
    nm text,
    abbrevnm text,
    vppid bigint,
    apid bigint,
    combpackcd bigint,
    legal_catcd bigint,
    subp text,
    disccd bigint,
    discdt date
);


--
-- Name: dmd_ap_info; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_ap_info (
    apid bigint,
    sz_weight text,
    colourcd bigint,
    prod_order_no text
);


--
-- Name: dmd_ap_ing; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_ap_ing (
    apid bigint,
    isid bigint,
    strnth double precision,
    uomcd bigint
);


--
-- Name: dmd_ccontent; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_ccontent (
    prntappid bigint,
    chldappid bigint,
    prntvppid bigint,
    chldvppid bigint
);


--
-- Name: dmd_control_info; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_control_info (
    vpid bigint,
    catcd bigint,
    catdt date,
    cat_prevcd bigint
);


--
-- Name: dmd_dform; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_dform (
    vpid bigint,
    formcd bigint
);


--
-- Name: dmd_droute; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_droute (
    vpid bigint,
    routecd bigint
);


--
-- Name: dmd_dtinfo; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_dtinfo (
    vppid bigint,
    pay_catcd bigint,
    price bigint,
    dt date,
    prevprice bigint
);


--
-- Name: dmd_gtin; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_gtin (
    appid bigint,
    startdt date,
    enddt date,
    gtin text
);


--
-- Name: dmd_ing; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_ing (
    isid bigint,
    isiddt date,
    isidprev bigint,
    invalid bigint,
    nm text
);


--
-- Name: dmd_lic_route; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lic_route (
    apid bigint,
    routecd bigint
);


--
-- Name: dmd_lookup_availability_restriction; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_availability_restriction (
    cd bigint,
    "desc" text
);


--
-- Name: dmd_lookup_basis_of_name; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_basis_of_name (
    cd bigint,
    "desc" text
);


--
-- Name: dmd_lookup_basis_of_strnth; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_basis_of_strnth (
    cd bigint,
    "desc" text
);


--
-- Name: dmd_lookup_colour; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_colour (
    cd bigint,
    "desc" text
);


--
-- Name: dmd_lookup_combination_pack_ind; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_combination_pack_ind (
    cd bigint,
    "desc" text
);


--
-- Name: dmd_lookup_combination_prod_ind; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_combination_prod_ind (
    cd bigint,
    "desc" text
);


--
-- Name: dmd_lookup_control_drug_category; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_control_drug_category (
    cd bigint,
    "desc" text
);


--
-- Name: dmd_lookup_df_indicator; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_df_indicator (
    cd bigint,
    "desc" text
);


--
-- Name: dmd_lookup_discontinued_ind; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_discontinued_ind (
    cd bigint,
    "desc" text
);


--
-- Name: dmd_lookup_dnd; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_dnd (
    cd bigint,
    "desc" text
);


--
-- Name: dmd_lookup_dt_payment_category; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_dt_payment_category (
    cd bigint,
    "desc" text
);


--
-- Name: dmd_lookup_flavour; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_flavour (
    cd bigint,
    "desc" text
);


--
-- Name: dmd_lookup_form; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_form (
    cd bigint,
    cddt date,
    cdprev bigint,
    "desc" text
);


--
-- Name: dmd_lookup_legal_category; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_legal_category (
    cd bigint,
    "desc" text
);


--
-- Name: dmd_lookup_licensing_authority; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_licensing_authority (
    cd bigint,
    "desc" text
);


--
-- Name: dmd_lookup_licensing_authority_change_reason; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_licensing_authority_change_reason (
    cd bigint,
    "desc" text
);


--
-- Name: dmd_lookup_namechange_reason; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_namechange_reason (
    cd bigint,
    "desc" text
);


--
-- Name: dmd_lookup_ont_form_route; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_ont_form_route (
    cd bigint,
    "desc" text
);


--
-- Name: dmd_lookup_price_basis; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_price_basis (
    cd bigint,
    "desc" text
);


--
-- Name: dmd_lookup_reimbursement_status; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_reimbursement_status (
    cd bigint,
    "desc" text
);


--
-- Name: dmd_lookup_route; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_route (
    cd bigint,
    cddt date,
    cdprev bigint,
    "desc" text
);


--
-- Name: dmd_lookup_spec_cont; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_spec_cont (
    cd bigint,
    "desc" text
);


--
-- Name: dmd_lookup_supplier; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_supplier (
    cd bigint,
    cddt date,
    cdprev bigint,
    invalid bigint,
    "desc" text
);


--
-- Name: dmd_lookup_unit_of_measure; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_unit_of_measure (
    cd bigint,
    cddt date,
    cdprev bigint,
    "desc" text
);


--
-- Name: dmd_lookup_virtual_product_non_avail; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_virtual_product_non_avail (
    cd bigint,
    "desc" text
);


--
-- Name: dmd_lookup_virtual_product_pres_status; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_lookup_virtual_product_pres_status (
    cd bigint,
    "desc" text
);


--
-- Name: dmd_ncsoconcession; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_ncsoconcession (
    id integer NOT NULL,
    drug character varying(400) NOT NULL,
    pack_size character varying(40) NOT NULL,
    price_concession_pence integer NOT NULL,
    vmpp_id bigint,
    date date NOT NULL
);


--
-- Name: dmd_ncsoconcession_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dmd_ncsoconcession_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dmd_ncsoconcession_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dmd_ncsoconcession_id_seq OWNED BY dmd_ncsoconcession.id;


--
-- Name: dmd_ont; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_ont (
    vpid bigint,
    formcd bigint
);


--
-- Name: dmd_pack_info; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_pack_info (
    appid bigint,
    reimb_statcd bigint,
    reimb_statdt date,
    reimb_statprevcd bigint,
    pack_order_no text
);


--
-- Name: dmd_prescrib_info; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_prescrib_info (
    appid bigint,
    sched_2 bigint,
    acbs bigint,
    padm bigint,
    fp10_mda bigint,
    sched_1 bigint,
    hosp bigint,
    nurse_f bigint,
    enurse_f bigint,
    dent_f bigint
);


--
-- Name: dmd_price_info; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_price_info (
    appid bigint,
    price bigint,
    pricedt date,
    price_prev bigint,
    price_basiscd bigint
);


--
-- Name: dmd_product; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_product (
    dmdid bigint NOT NULL,
    bnf_code text,
    vpid bigint,
    name character varying(400),
    full_name text,
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


--
-- Name: dmd_product_temp; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_product_temp (
    dmdid bigint NOT NULL,
    bnf_code text,
    vpid bigint,
    name text,
    full_name text,
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


--
-- Name: dmd_reimb_info; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_reimb_info (
    appid bigint,
    px_chrgs bigint,
    disp_fees bigint,
    bb bigint,
    ltd_stab bigint,
    cal_pack bigint,
    spec_contcd bigint,
    dnd bigint,
    fp34d bigint
);


--
-- Name: dmd_tariffprice; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_tariffprice (
    id integer NOT NULL,
    date date NOT NULL,
    price_pence integer NOT NULL,
    product_id bigint NOT NULL,
    tariff_category_id integer NOT NULL,
    vmpp_id bigint NOT NULL
);


--
-- Name: dmd_tariffprice_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE dmd_tariffprice_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dmd_tariffprice_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE dmd_tariffprice_id_seq OWNED BY dmd_tariffprice.id;


--
-- Name: dmd_vmp; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_vmp (
    vpid bigint NOT NULL,
    vpiddt date,
    vpidprev bigint,
    vtmid bigint,
    invalid bigint,
    nm text,
    abbrevnm text,
    basiscd bigint,
    nmdt date,
    nmprev text,
    basis_prevcd bigint,
    nmchangecd bigint,
    combprodcd bigint,
    pres_statcd bigint,
    sug_f bigint,
    glu_f bigint,
    pres_f bigint,
    cfc_f bigint,
    non_availcd bigint,
    non_availdt date,
    df_indcd bigint,
    udfs double precision,
    udfs_uomcd bigint,
    unit_dose_uomcd bigint
);


--
-- Name: dmd_vmpp; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_vmpp (
    vppid bigint NOT NULL,
    invalid bigint,
    nm text,
    abbrevnm text,
    vpid bigint,
    qtyval double precision,
    qty_uomcd bigint,
    combpackcd bigint
);


--
-- Name: dmd_vpi; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_vpi (
    vpid bigint,
    isid bigint,
    basis_strntcd bigint,
    bs_subid bigint,
    strnt_nmrtr_val double precision,
    strnt_nmrtr_uomcd bigint,
    strnt_dnmtr_val double precision,
    strnt_dnmtr_uomcd bigint
);


--
-- Name: dmd_vtm; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE dmd_vtm (
    vtmid bigint,
    invalid bigint,
    nm text,
    abbrevnm text,
    vtmidprev text,
    vtmiddt date
);


--
-- Name: dmd_ncsoconcession id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dmd_ncsoconcession ALTER COLUMN id SET DEFAULT nextval('dmd_ncsoconcession_id_seq'::regclass);


--
-- Name: dmd_tariffprice id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY dmd_tariffprice ALTER COLUMN id SET DEFAULT nextval('dmd_tariffprice_id_seq'::regclass);


--
-- Name: dmd_amp dmd_amp_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dmd_amp
    ADD CONSTRAINT dmd_amp_pkey PRIMARY KEY (apid);


--
-- Name: dmd_ampp dmd_ampp_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dmd_ampp
    ADD CONSTRAINT dmd_ampp_pkey PRIMARY KEY (appid);


--
-- Name: dmd_ncsoconcession dmd_ncsoconcession_date_a1a20bea_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dmd_ncsoconcession
    ADD CONSTRAINT dmd_ncsoconcession_date_a1a20bea_uniq UNIQUE (date, vmpp_id);


--
-- Name: dmd_ncsoconcession dmd_ncsoconcession_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dmd_ncsoconcession
    ADD CONSTRAINT dmd_ncsoconcession_pkey PRIMARY KEY (id);


--
-- Name: dmd_product dmd_product_temp_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dmd_product
    ADD CONSTRAINT dmd_product_temp_pkey PRIMARY KEY (dmdid);


--
-- Name: dmd_product_temp dmd_product_temp_pkey1; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dmd_product_temp
    ADD CONSTRAINT dmd_product_temp_pkey1 PRIMARY KEY (dmdid);


--
-- Name: dmd_tariffprice dmd_tariffprice_date_a7f529c9_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dmd_tariffprice
    ADD CONSTRAINT dmd_tariffprice_date_a7f529c9_uniq UNIQUE (date, vmpp_id);


--
-- Name: dmd_tariffprice dmd_tariffprice_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dmd_tariffprice
    ADD CONSTRAINT dmd_tariffprice_pkey PRIMARY KEY (id);


--
-- Name: dmd_vmp dmd_vmp_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dmd_vmp
    ADD CONSTRAINT dmd_vmp_pkey PRIMARY KEY (vpid);


--
-- Name: dmd_vmpp dmd_vmpp_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dmd_vmpp
    ADD CONSTRAINT dmd_vmpp_pkey PRIMARY KEY (vppid);


--
-- Name: dmd_ncsoconcession_26eb061f; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dmd_ncsoconcession_26eb061f ON dmd_ncsoconcession USING btree (vmpp_id);


--
-- Name: dmd_ncsoconcession_5fc73231; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dmd_ncsoconcession_5fc73231 ON dmd_ncsoconcession USING btree (date);


--
-- Name: dmd_tariffprice_26eb061f; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dmd_tariffprice_26eb061f ON dmd_tariffprice USING btree (vmpp_id);


--
-- Name: dmd_tariffprice_53e32515; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dmd_tariffprice_53e32515 ON dmd_tariffprice USING btree (tariff_category_id);


--
-- Name: dmd_tariffprice_5fc73231; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dmd_tariffprice_5fc73231 ON dmd_tariffprice USING btree (date);


--
-- Name: dmd_tariffprice_9bea82de; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX dmd_tariffprice_9bea82de ON dmd_tariffprice USING btree (product_id);


--
-- Name: i_bnf_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX i_bnf_code ON dmd_product_temp USING btree (bnf_code);


--
-- Name: i_dmd_amp_vpid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX i_dmd_amp_vpid ON dmd_amp USING btree (vpid);


--
-- Name: i_dmd_ampp_apid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX i_dmd_ampp_apid ON dmd_ampp USING btree (apid);


--
-- Name: i_dmd_ampp_vppid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX i_dmd_ampp_vppid ON dmd_ampp USING btree (vppid);


--
-- Name: i_dmd_ap_info_apid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX i_dmd_ap_info_apid ON dmd_ap_info USING btree (apid);


--
-- Name: i_dmd_ap_ing_apid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX i_dmd_ap_ing_apid ON dmd_ap_ing USING btree (apid);


--
-- Name: i_dmd_control_info_vpid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX i_dmd_control_info_vpid ON dmd_control_info USING btree (vpid);


--
-- Name: i_dmd_dform_vpid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX i_dmd_dform_vpid ON dmd_dform USING btree (vpid);


--
-- Name: i_dmd_droute_vpid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX i_dmd_droute_vpid ON dmd_droute USING btree (vpid);


--
-- Name: i_dmd_dtinfo_vppid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX i_dmd_dtinfo_vppid ON dmd_dtinfo USING btree (vppid);


--
-- Name: i_dmd_lic_route_apid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX i_dmd_lic_route_apid ON dmd_lic_route USING btree (apid);


--
-- Name: i_dmd_ont_vpid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX i_dmd_ont_vpid ON dmd_ont USING btree (vpid);


--
-- Name: i_dmd_pack_info_appid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX i_dmd_pack_info_appid ON dmd_pack_info USING btree (appid);


--
-- Name: i_dmd_prescrib_info_appid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX i_dmd_prescrib_info_appid ON dmd_prescrib_info USING btree (appid);


--
-- Name: i_dmd_price_info_appid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX i_dmd_price_info_appid ON dmd_price_info USING btree (appid);


--
-- Name: i_dmd_reimb_info_appid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX i_dmd_reimb_info_appid ON dmd_reimb_info USING btree (appid);


--
-- Name: i_dmd_vmpp_vpid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX i_dmd_vmpp_vpid ON dmd_vmpp USING btree (vpid);


--
-- Name: i_dmd_vpi_vpid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX i_dmd_vpi_vpid ON dmd_vpi USING btree (vpid);


--
-- Name: i_dmdid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX i_dmdid ON dmd_product_temp USING btree (dmdid);


--
-- Name: i_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX i_name ON dmd_product_temp USING btree (name);


--
-- Name: i_vpid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX i_vpid ON dmd_product_temp USING btree (vpid);


--
-- Name: dmd_tariffprice dmd_tariffprice_product_id_39bb1b2e_fk_dmd_product_dmdid; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY dmd_tariffprice
    ADD CONSTRAINT dmd_tariffprice_product_id_39bb1b2e_fk_dmd_product_dmdid FOREIGN KEY (product_id) REFERENCES dmd_product(dmdid) DEFERRABLE INITIALLY DEFERRED;


--
-- PostgreSQL database dump complete
--
