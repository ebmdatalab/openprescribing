SELECT * FROM {project}.{hscic}.prescribing_v1 WHERE month < '2015-01-01'
UNION ALL
SELECT * FROM {project}.{hscic}.prescribing_v2
