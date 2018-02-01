SELECT
  month,
  practice,
  pct,
  SUM(quantity*dose_per_unit*ome_multiplier) AS total_ome
FROM
  {project}.{hscic}.normalised_prescribing_standard AS presc
JOIN
  -- data in richard.opioid_measure comes from:
  -- https://docs.google.com/spreadsheets/d/1IjnHbYVszZKPmVSYydtMVzbDLPOmq8bOFq45QsSu6sE/edit?usp=sharing
  ebmdatalab.richard.opioid_measure as opioid
ON
  CONCAT(SUBSTR(presc.bnf_code,0,9),'AA%',(SUBSTR(presc.bnf_code,-2,2)))=CONCAT(SUBSTR(opioid.bnf_code,0,11),'%',(SUBSTR(opioid.bnf_code,-2,2)))
GROUP BY
  month,
  pct,
  practice
