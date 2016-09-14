SELECT
  local.denom_cost -
    ((global.p_50th * local.denom_quantity * IF(local.num_quantity > 0, (local.num_cost / local.num_quantity), global.cost_per_num))
     + ((local.denom_quantity - (local.denom_quantity * global.p_50th))
        * IF((local.denom_quantity - local.num_quantity) = 0, global.cost_per_denom, ((local.denom_cost - local.num_cost) / (local.denom_quantity - local.num_quantity)))
        )
     ) AS saving_at_50th,
  local.*
FROM
  {local_table} AS local
LEFT JOIN
  {global_table} global
ON
  (global.month = local.month)
