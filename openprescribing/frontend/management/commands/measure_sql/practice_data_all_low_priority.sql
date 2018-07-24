SELECT
  TIMESTAMP(month) AS month,
  practice_id AS practice,
  numerator,
  denominator
FROM
  {project}.{measures}.practice_data_lpcoprox

UNION ALL
SELECT
  TIMESTAMP(month) AS month,
  practice_id AS practice,
  numerator,
  denominator
FROM
  {project}.{measures}.practice_data_lpdosulepin

UNION ALL
SELECT
  TIMESTAMP(month) AS month,
  practice_id AS practice,
  numerator,
  denominator
FROM
  {project}.{measures}.practice_data_lpdoxazosin

UNION ALL
SELECT
  TIMESTAMP(month) AS month,
  practice_id AS practice,
  numerator,
  denominator
FROM
  {project}.{measures}.practice_data_lpfentanylir

UNION ALL
SELECT
  TIMESTAMP(month) AS month,
  practice_id AS practice,
  numerator,
  denominator
FROM
  {project}.{measures}.practice_data_lpglucosamine

UNION ALL
SELECT
  TIMESTAMP(month) AS month,
  practice_id AS practice,
  numerator,
  denominator
FROM
  {project}.{measures}.practice_data_lphomeopathy

UNION ALL
SELECT
  TIMESTAMP(month) AS month,
  practice_id AS practice,
  numerator,
  denominator
FROM
  {project}.{measures}.practice_data_lplidocaine

UNION ALL
SELECT
  TIMESTAMP(month) AS month,
  practice_id AS practice,
  numerator,
  denominator
FROM
  {project}.{measures}.practice_data_lpliothyronine

UNION ALL
SELECT
  TIMESTAMP(month) AS month,
  practice_id AS practice,
  numerator,
  denominator
FROM
  {project}.{measures}.practice_data_lplutein

UNION ALL
SELECT
  TIMESTAMP(month) AS month,
  practice_id AS practice,
  numerator,
  denominator
FROM
  {project}.{measures}.practice_data_lpomega3

UNION ALL
SELECT
  TIMESTAMP(month) AS month,
  practice_id AS practice,
  numerator,
  denominator
FROM
  {project}.{measures}.practice_data_lpoxycodone

UNION ALL
SELECT
  TIMESTAMP(month) AS month,
  practice_id AS practice,
  numerator,
  denominator
FROM
  {project}.{measures}.practice_data_lpperindopril

UNION ALL
SELECT
  TIMESTAMP(month) AS month,
  practice_id AS practice,
  numerator,
  denominator
FROM
  {project}.{measures}.practice_data_lprubefacients

UNION ALL
SELECT
  TIMESTAMP(month) AS month,
  practice_id AS practice,
  numerator,
  denominator
FROM
  {project}.{measures}.practice_data_lptadalafil

UNION ALL
SELECT
  TIMESTAMP(month) AS month,
  practice_id AS practice,
  numerator,
  denominator
FROM
  {project}.{measures}.practice_data_lptramadolpara

UNION ALL
SELECT
  TIMESTAMP(month) AS month,
  practice_id AS practice,
  numerator,
  denominator
FROM
  {project}.{measures}.practice_data_lptravelvacs

UNION ALL
SELECT
  TIMESTAMP(month) AS month,
  practice_id AS practice,
  numerator,
  denominator
FROM
  {project}.{measures}.practice_data_lptrimipramine
