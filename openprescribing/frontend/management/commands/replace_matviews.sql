BEGIN;
DROP MATERIALIZED VIEW IF EXISTS vw__presentation_summary ;
CREATE TABLE IF NOT EXISTS vw__presentation_summary (
  processing_date date,
  presentation_code character varying(15),
  items bigint,
  cost double precision,
  quantity bigint);

CREATE INDEX IF NOT EXISTS vw__idx_presentation_summary
  ON vw__presentation_summary(presentation_code varchar_pattern_ops);

DROP MATERIALIZED VIEW IF EXISTS vw__presentation_summary_by_ccg;
CREATE TABLE IF NOT EXISTS vw__presentation_summary_by_ccg (
  processing_date date,
  pct_id character varying(3),
  presentation_code character varying(15),
  items bigint,
  cost double precision,
  quantity bigint);

CREATE INDEX IF NOT EXISTS vw__idx_pres_by_ccg_pres_code
   ON vw__presentation_summary_by_ccg (presentation_code varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS vw__idx_pres_by_ccg_joint_code
   ON vw__presentation_summary_by_ccg(pct_id, presentation_code);


DROP MATERIALIZED VIEW IF EXISTS vw__chemical_summary_by_ccg;
CREATE TABLE IF NOT EXISTS vw__chemical_summary_by_ccg (
  processing_date date,
  pct_id character varying(3),
  chemical_id character varying(9),
  items bigint,
  cost double precision,
  quantity bigint);

CREATE INDEX IF NOT EXISTS vw__idx_chem_by_ccg
  ON vw__chemical_summary_by_ccg(chemical_id varchar_pattern_ops, pct_id);
CREATE INDEX IF NOT EXISTS vw__idx_ccg_by_chem
  ON vw__chemical_summary_by_ccg(pct_id, chemical_id varchar_pattern_ops);

DROP MATERIALIZED VIEW IF EXISTS vw__chemical_summary_by_practice;
CREATE TABLE IF NOT EXISTS vw__chemical_summary_by_practice (
  processing_date date,
  practice_id character varying(6),
  chemical_id character varying(9),
  items bigint,
  cost double precision,
  quantity bigint);

CREATE INDEX IF NOT EXISTS vw__idx_practice_by_chem
  ON vw__chemical_summary_by_practice (chemical_id varchar_pattern_ops, practice_id);
CREATE INDEX IF NOT EXISTS vw__idx_chem_by_practice
  ON vw__chemical_summary_by_practice (practice_id, chemical_id varchar_pattern_ops);
CREATE INDEX IF NOT EXISTS idx_chem_by_practice_bydate
  ON vw__chemical_summary_by_practice (chemical_id varchar_pattern_ops, processing_date);

DROP MATERIALIZED VIEW IF EXISTS vw__practice_summary;
CREATE TABLE IF NOT EXISTS vw__practice_summary (
  processing_date date,
  practice_id character varying(6),
  items bigint,
  cost double precision,
  quantity bigint);

CREATE INDEX IF NOT EXISTS vw__practice_summary_prac_id ON vw__practice_summary(practice_id);


DROP MATERIALIZED VIEW IF EXISTS vw__ccgstatistics;
CREATE TABLE IF NOT EXISTS vw__ccgstatistics (
  date date,
  pct_id character varying(3),
  name character varying(200),
  total_list_size numeric,
  astro_pu_items double precision,
  astro_pu_cost double precision,
  star_pu json
);

CREATE INDEX IF NOT EXISTS vw__idx_ccgstatistics_by_ccg ON vw__ccgstatistics(pct_id);
COMMIT;
