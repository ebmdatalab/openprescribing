-- Restrictions on availability of AMP
-- Section 6 of Implementation Guide (p48)

update dmd_product
set avail_restrictcd = 1
where dmdid in (
  select dmdid
  from dmd_product
  inner join dmd_amp
  on dmd_amp.vpid = dmdid
  where dmd_amp.avail_restrictcd = 1
);


UPDATE dmd_product
SET avail_restrictcd = subquery.avail_restrictcd2
FROM (
  SELECT
    dmd_product.*,
    dmd_amp.avail_restrictcd AS avail_restrictcd2
  FROM
    dmd_product
  INNER JOIN
    dmd_amp
  ON
    dmd_amp.vpid = dmd_product.dmdid
  WHERE
    dmd_amp.avail_restrictcd != 1
  AND
    dmd_amp.avail_restrictcd != 9
  AND
    dmd_product.avail_restrictcd IS NULL)
AS subquery
WHERE
  subquery.dmdid = dmd_product.dmdid;

update dmd_product
set avail_restrictcd = 9
where dmdid in (
  select dmdid
  from dmd_product
  where dmd_product.avail_restrictcd is null
);
