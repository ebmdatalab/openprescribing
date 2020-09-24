-- This SQL is checked in to the git repo at measure_sql/gaba_total_ddd.sql.
-- Do not make changes directly in BQ!  Instead, change the version in the repo and run
--
--     ./manage.py create_bq_measure_views

SELECT
  month,
  practice,
  pct,
  SUM(gaba_ddd) AS gaba_ddd
FROM (
  SELECT
    month,
    practice,
    pct,
    SUM(CASE --this calculates the mg of gabapentin for each presentation
        WHEN bnf_code LIKE '0408010G0%AA' THEN quantity *100 --Gabapentin_Cap 100mg (brands and generic)
        WHEN bnf_code LIKE '0408010G0%AB' THEN quantity *300 --Gabapentin_Cap 300mg (brands and generic)
        WHEN bnf_code LIKE '0408010G0%AC' THEN quantity *400 --Gabapentin_Cap 400mg (brands and generic)
        WHEN bnf_code LIKE '0408010G0%AD' THEN quantity *50 --Gabapentin_Pdrs 50mg (brands and generic)
        WHEN bnf_code LIKE '0408010G0%AE' THEN quantity *150 --Gabapentin_Pdrs 150mg (brands and generic)
        WHEN bnf_code LIKE '0408010G0%AF' THEN quantity *400 --Gabapentin_Pdrs 400mg (brands and generic)
        WHEN bnf_code LIKE '0408010G0%AG' THEN quantity *20 --Gabapentin_Liq Spec 100mg/5ml (brands and generic)
        WHEN bnf_code LIKE '0408010G0%AH' THEN quantity *300 --Gabapentin_Cap 300mg @gn (brands and generic)
        WHEN bnf_code LIKE '0408010G0%AI' THEN quantity *240 --Gabapentin_Pdrs 240mg (brands and generic)
        WHEN bnf_code LIKE '0408010G0%AJ' THEN quantity *600 --Gabapentin_Tab 600mg (brands and generic)
        WHEN bnf_code LIKE '0408010G0%AK' THEN quantity *800 --Gabapentin_Tab 800mg (brands and generic)
        WHEN bnf_code LIKE '0408010G0%AL' THEN quantity *100 --Gabapentin_Cap 100mg @gn (brands and generic)
        WHEN bnf_code LIKE '0408010G0%AM' THEN quantity *400 --Gabapentin_Cap 400mg @gn (brands and generic)
        WHEN bnf_code LIKE '0408010G0%AN' THEN quantity *30 --Gabapentin_Liq Spec 150mg/5ml (brands and generic)
        WHEN bnf_code LIKE '0408010G0%AP' THEN quantity *60 --Gabapentin_Liq Spec 300mg/5ml (brands and generic)
        WHEN bnf_code LIKE '0408010G0%AQ' THEN quantity *50 --Gabapentin_Liq Spec 250mg/5ml (brands and generic)
        WHEN bnf_code LIKE '0408010G0%AR' THEN quantity *90 --Gabapentin_Liq Spec 450mg/5ml (brands and generic)
        WHEN bnf_code LIKE '0408010G0%AS' THEN quantity *10 --Gabapentin_Liq Spec 50mg/5ml (brands and generic)
        WHEN bnf_code LIKE '0408010G0%AT' THEN quantity *50 --Gabapentin_Oral Soln 250mg/5ml (brands and generic)
        WHEN bnf_code LIKE '0408010G0%AU' THEN quantity *50 --Gabapentin_Cap 50mg (brands and generic)
        WHEN bnf_code LIKE '0408010G0%AV' THEN quantity *100 --Gabapentin_Liq Spec 500mg/5ml (brands and generic)
        WHEN bnf_code LIKE '0408010G0%AW' THEN quantity *40 --Gabapentin_Liq Spec 200mg/5ml (brands and generic)
        WHEN bnf_code LIKE '0408010G0%AY' THEN quantity *80 --Gabapentin_Liq Spec 400mg/5ml (brands and generic)
        WHEN bnf_code LIKE '0408010G0%AZ' THEN quantity *140 --Gabapentin_Liq Spec 700mg/5ml (brands and generic)
        WHEN bnf_code LIKE '0408010G0%BA' THEN quantity *180 --Gabapentin_Liq Spec 900mg/5ml (brands and generic)
        WHEN bnf_code LIKE '0408010G0%BB' THEN quantity *120 --Gabapentin_Liq Spec 600mg/5ml (brands and generic)
        WHEN bnf_code LIKE '0408010G0%BC' THEN quantity *160 --Gabapentin_Liq Spec 800mg/5ml (brands and generic)
        WHEN bnf_code LIKE '0408010G0%BD' THEN quantity *50 --Gabapentin_Oral Susp 250mg/5ml (brands and generic)
        WHEN bnf_code LIKE '0408010G0%BE' THEN quantity *80 --Gabapentin_Oral Soln 400mg/5ml (brands and generic)
        WHEN bnf_code LIKE '0408010G0%BF' THEN quantity *80 --Gabapentin_Oral Susp 400mg/5ml (brands and generic)
        WHEN bnf_code LIKE '0408010G0%BG' THEN quantity *50 --Gabapentin_Oral Soln 50mg/ml S/F (brands and generic)
      ELSE
      0
    END
      )/1800 AS gaba_ddd -- and divides all by 1800 to get DDD (https://www.whocc.no/atc_ddd_index/?code=N03AX12)
  FROM
    {project}.{hscic}.normalised_prescribing
  WHERE
    bnf_code LIKE '0408010G0%' --gabapentin
  GROUP BY
    month,
    practice,
    pct
  UNION ALL
  SELECT
    month,
    practice,
    pct,
    (SUM(lyrica_mg)/300) AS gaba_ddd
  FROM
    {project}.{measures}.pregabalin_total_mg AS rx --this is from the existing pregabalinmg query, so divide by 300 to get DDD for pregabalin https://www.whocc.no/atc_ddd_index/?code=N03AX16
  GROUP BY
    month,
    practice,
    pct)
GROUP BY
  month,
  practice,
  pct
ORDER BY
  practice,
  month
