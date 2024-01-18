-- This SQL is checked in to the git repo at measure_sql/vw__measure_conversion.sql.
-- Do not make changes directly in BQ!  Instead, change the version in the repo and run
--
--     ./manage.py create_bq_measure_views

SELECT cd, descr,
CASE  
      WHEN cd = 258682000 THEN 0.001 -- convert microgram to milligram
      WHEN cd = 258685003 THEN 1000  -- convert gram to milligram
      WHEN cd = 258684004 THEN 1     -- milligram base value
      ELSE null END AS nmtr_unit_conversion,
CASE  
      WHEN cd = 258770004 THEN 0.001 -- convert litre to millilitre
      WHEN cd = 258774008 THEN 1000  -- convert microlitre to millilitre
      WHEN cd = 258773002 THEN 1     -- millilitre base value
      ELSE null END AS dnmtr_unit_conversion
FROM dmd.unitofmeasure
ORDER BY descr
