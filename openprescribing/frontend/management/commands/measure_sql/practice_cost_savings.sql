SELECT
  local.denom_cost -
    ((global.practice_10th * local.denom_quantity * IF(local.num_quantity > 0, (local.num_cost / local.num_quantity), global.cost_per_num))
     + ((local.denom_quantity - (local.denom_quantity * global.practice_10th))
        * IF((local.denom_quantity - COALESCE(local.num_quantity, 0)) = 0, global.cost_per_denom, ((local.denom_cost - COALESCE(local.num_cost, 0)) / (local.denom_quantity - COALESCE(local.num_quantity, 0))))
        )
     ) AS cost_savings_10,
  local.denom_cost -
    ((global.practice_20th * local.denom_quantity * IF(local.num_quantity > 0, (local.num_cost / local.num_quantity), global.cost_per_num))
     + ((local.denom_quantity - (local.denom_quantity * global.practice_20th))
        * IF((local.denom_quantity - COALESCE(local.num_quantity, 0)) = 0, global.cost_per_denom, ((local.denom_cost - COALESCE(local.num_cost, 0)) / (local.denom_quantity - COALESCE(local.num_quantity, 0))))
        )
     ) AS cost_savings_20,
  local.denom_cost -
    ((global.practice_30th * local.denom_quantity * IF(local.num_quantity > 0, (local.num_cost / local.num_quantity), global.cost_per_num))
     + ((local.denom_quantity - (local.denom_quantity * global.practice_30th))
        * IF((local.denom_quantity - COALESCE(local.num_quantity, 0)) = 0, global.cost_per_denom, ((local.denom_cost - COALESCE(local.num_cost, 0)) / (local.denom_quantity - COALESCE(local.num_quantity, 0))))
        )
     ) AS cost_savings_30,
  local.denom_cost -
    ((global.practice_40th * local.denom_quantity * IF(local.num_quantity > 0, (local.num_cost / local.num_quantity), global.cost_per_num))
     + ((local.denom_quantity - (local.denom_quantity * global.practice_40th))
        * IF((local.denom_quantity - COALESCE(local.num_quantity, 0)) = 0, global.cost_per_denom, ((local.denom_cost - COALESCE(local.num_cost, 0)) / (local.denom_quantity - COALESCE(local.num_quantity, 0))))
        )
     ) AS cost_savings_40,
  local.denom_cost -
    ((global.practice_50th * local.denom_quantity * IF(local.num_quantity > 0, (local.num_cost / local.num_quantity), global.cost_per_num))
     + ((local.denom_quantity - (local.denom_quantity * global.practice_50th))
        * IF((local.denom_quantity - COALESCE(local.num_quantity, 0)) = 0, global.cost_per_denom, ((local.denom_cost - COALESCE(local.num_cost, 0)) / (local.denom_quantity - COALESCE(local.num_quantity, 0))))
        )
     ) AS cost_savings_50,
  local.denom_cost -
    ((global.practice_60th * local.denom_quantity * IF(local.num_quantity > 0, (local.num_cost / local.num_quantity), global.cost_per_num))
     + ((local.denom_quantity - (local.denom_quantity * global.practice_60th))
        * IF((local.denom_quantity - COALESCE(local.num_quantity, 0)) = 0, global.cost_per_denom, ((local.denom_cost - COALESCE(local.num_cost, 0)) / (local.denom_quantity - COALESCE(local.num_quantity, 0))))
        )
     ) AS cost_savings_60,
  local.denom_cost -
    ((global.practice_70th * local.denom_quantity * IF(local.num_quantity > 0, (local.num_cost / local.num_quantity), global.cost_per_num))
     + ((local.denom_quantity - (local.denom_quantity * global.practice_70th))
        * IF((local.denom_quantity - COALESCE(local.num_quantity, 0)) = 0, global.cost_per_denom, ((local.denom_cost - COALESCE(local.num_cost, 0)) / (local.denom_quantity - COALESCE(local.num_quantity, 0))))
        )
     ) AS cost_savings_70,
  local.denom_cost -
    ((global.practice_80th * local.denom_quantity * IF(local.num_quantity > 0, (local.num_cost / local.num_quantity), global.cost_per_num))
     + ((local.denom_quantity - (local.denom_quantity * global.practice_80th))
        * IF((local.denom_quantity - COALESCE(local.num_quantity, 0)) = 0, global.cost_per_denom, ((local.denom_cost - COALESCE(local.num_cost, 0)) / (local.denom_quantity - COALESCE(local.num_quantity, 0))))
        )
     ) AS cost_savings_80,
  local.denom_cost -
    ((global.practice_90th * local.denom_quantity * IF(local.num_quantity > 0, (local.num_cost / local.num_quantity), global.cost_per_num))
     + ((local.denom_quantity - (local.denom_quantity * global.practice_90th))
        * IF((local.denom_quantity - COALESCE(local.num_quantity, 0)) = 0, global.cost_per_denom, ((local.denom_cost - COALESCE(local.num_cost, 0)) / (local.denom_quantity - COALESCE(local.num_quantity, 0))))
        )
     ) AS cost_savings_90,
  local.*
FROM
  {local_table} AS local
LEFT JOIN
  {global_table} global
ON
  (global.month = local.month)
