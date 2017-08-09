-- whether an item is a controlled drug and if so to which
-- category it belongs
-- Section 6 of Implementation Guide (p52)

update dmd_product_temp
set catcd = subquery.catcd2
from (SELECT dmd_product_temp.*, dmd_control_info.catcd AS catcd2 FROM dmd_product_temp
inner join dmd_vmp
on dmd_vmp.vpid = dmd_product_temp.vpid
inner join dmd_control_info
on dmd_control_info.vpid = dmd_vmp.vpid) AS subquery
WHERE dmd_product_temp.dmdid = subquery.dmdid
