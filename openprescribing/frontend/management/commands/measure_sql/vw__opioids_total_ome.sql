-- This SQL is checked in to the git repo at measure_sql/vw__opioids_total_ome.sql.
-- Do not make changes directly in BQ!  Instead, change the version in the repo and run
--
--     ./manage.py create_bq_measure_views

SELECT month, 
       practice, 
       pct, 
       SUM(ome_dose)AS total_ome 
FROM   measures.vw__opioid_measure_dmd 
GROUP  BY month, 
          practice, 
          pct 
