-- Restrictions on availability of AMP
-- Section 6 of Implementation Guide (p48)

update dmd_product_temp
set avail_restrictcd = 1
where dmdid in (
  select dmdid
  from dmd_product_temp
  inner join dmd_amp
  on dmd_amp.vpid = dmdid
  where dmd_amp.avail_restrictcd = 1
);


UPDATE dmd_product_temp
SET avail_restrictcd = subquery.avail_restrictcd2
FROM (
  SELECT
    dmd_product_temp.*,
    dmd_amp.avail_restrictcd AS avail_restrictcd2
  FROM
    dmd_product_temp
  INNER JOIN
    dmd_amp
  ON
    dmd_amp.vpid = dmd_product_temp.dmdid
  WHERE
    dmd_amp.avail_restrictcd != 1
  AND
    dmd_amp.avail_restrictcd != 9
  AND
    dmd_product_temp.avail_restrictcd IS NULL)
AS subquery
WHERE
  subquery.dmdid = dmd_product_temp.dmdid;

update dmd_product_temp
set avail_restrictcd = 9
where dmdid in (
  select dmdid
  from dmd_product_temp
  where dmd_product_temp.avail_restrictcd is null
);
