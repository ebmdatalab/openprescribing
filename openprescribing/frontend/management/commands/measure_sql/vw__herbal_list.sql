  -- This SQL is checked in to the git repo at measure_sql/vw__herbal_list.sql.
-- Do not make changes directly in BQ!  Instead, change the version in the repo and run
--
--     ./manage.py create_bq_measure_views

SELECT
  bnf_code
FROM
  {project}.{dmd}.amp
WHERE
  lic_auth = 4
  AND bnf_code NOT LIKE '190203%'
GROUP BY
  bnf_code
