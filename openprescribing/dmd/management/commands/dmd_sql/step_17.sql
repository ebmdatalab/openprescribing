DELETE FROM dmd_product
WHERE
    dmdid NOT IN (SELECT dmdid FROM dmd_product_temp)
    AND dmdid NOT IN (10000000000, 10000000001);
