SELECT * FROM {projects}.{hscic}.prescribing_v1 WHERE month < '2015-01-01'
UNION ALL
SELECT * FROM {projects}.{hscic}.prescribing_v2
