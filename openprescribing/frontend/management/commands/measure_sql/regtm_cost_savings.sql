SELECT
  local.denom_cost -
    ((global.regtm_10th * local.denom_quantity * IF(local.num_quantity > 0, (local.num_cost / local.num_quantity), global.cost_per_num))
     + ((local.denom_quantity - (local.denom_quantity * global.regtm_10th))
        * IF((local.denom_quantity - COALESCE(local.num_quantity, 0)) = 0, global.cost_per_denom, ((local.denom_cost - COALESCE(local.num_cost, 0)) / (local.denom_quantity - COALESCE(local.num_quantity, 0))))
        )
     ) AS cost_savings_10,
  local.denom_cost -
    ((global.regtm_20th * local.denom_quantity * IF(local.num_quantity > 0, (local.num_cost / local.num_quantity), global.cost_per_num))
     + ((local.denom_quantity - (local.denom_quantity * global.regtm_20th))
        * IF((local.denom_quantity - COALESCE(local.num_quantity, 0)) = 0, global.cost_per_denom, ((local.denom_cost - COALESCE(local.num_cost, 0)) / (local.denom_quantity - COALESCE(local.num_quantity, 0))))
        )
     ) AS cost_savings_20,
  local.denom_cost -
    ((global.regtm_30th * local.denom_quantity * IF(local.num_quantity > 0, (local.num_cost / local.num_quantity), global.cost_per_num))
     + ((local.denom_quantity - (local.denom_quantity * global.regtm_30th))
        * IF((local.denom_quantity - COALESCE(local.num_quantity, 0)) = 0, global.cost_per_denom, ((local.denom_cost - COALESCE(local.num_cost, 0)) / (local.denom_quantity - COALESCE(local.num_quantity, 0))))
        )
     ) AS cost_savings_30,
  local.denom_cost -
    ((global.regtm_40th * local.denom_quantity * IF(local.num_quantity > 0, (local.num_cost / local.num_quantity), global.cost_per_num))
     + ((local.denom_quantity - (local.denom_quantity * global.regtm_40th))
        * IF((local.denom_quantity - COALESCE(local.num_quantity, 0)) = 0, global.cost_per_denom, ((local.denom_cost - COALESCE(local.num_cost, 0)) / (local.denom_quantity - COALESCE(local.num_quantity, 0))))
        )
     ) AS cost_savings_40,
  local.denom_cost -
    ((global.regtm_50th * local.denom_quantity * IF(local.num_quantity > 0, (local.num_cost / local.num_quantity), global.cost_per_num))
     + ((local.denom_quantity - (local.denom_quantity * global.regtm_50th))
        * IF((local.denom_quantity - COALESCE(local.num_quantity, 0)) = 0, global.cost_per_denom, ((local.denom_cost - COALESCE(local.num_cost, 0)) / (local.denom_quantity - COALESCE(local.num_quantity, 0))))
        )
     ) AS cost_savings_50,
  local.denom_cost -
    ((global.regtm_60th * local.denom_quantity * IF(local.num_quantity > 0, (local.num_cost / local.num_quantity), global.cost_per_num))
     + ((local.denom_quantity - (local.denom_quantity * global.regtm_60th))
        * IF((local.denom_quantity - COALESCE(local.num_quantity, 0)) = 0, global.cost_per_denom, ((local.denom_cost - COALESCE(local.num_cost, 0)) / (local.denom_quantity - COALESCE(local.num_quantity, 0))))
        )
     ) AS cost_savings_60,
  local.denom_cost -
    ((global.regtm_70th * local.denom_quantity * IF(local.num_quantity > 0, (local.num_cost / local.num_quantity), global.cost_per_num))
     + ((local.denom_quantity - (local.denom_quantity * global.regtm_70th))
        * IF((local.denom_quantity - COALESCE(local.num_quantity, 0)) = 0, global.cost_per_denom, ((local.denom_cost - COALESCE(local.num_cost, 0)) / (local.denom_quantity - COALESCE(local.num_quantity, 0))))
        )
     ) AS cost_savings_70,
  local.denom_cost -
    ((global.regtm_80th * local.denom_quantity * IF(local.num_quantity > 0, (local.num_cost / local.num_quantity), global.cost_per_num))
     + ((local.denom_quantity - (local.denom_quantity * global.regtm_80th))
        * IF((local.denom_quantity - COALESCE(local.num_quantity, 0)) = 0, global.cost_per_denom, ((local.denom_cost - COALESCE(local.num_cost, 0)) / (local.denom_quantity - COALESCE(local.num_quantity, 0))))
        )
     ) AS cost_savings_80,
  local.denom_cost -
    ((global.regtm_90th * local.denom_quantity * IF(local.num_quantity > 0, (local.num_cost / local.num_quantity), global.cost_per_num))
     + ((local.denom_quantity - (local.denom_quantity * global.regtm_90th))
        * IF((local.denom_quantity - COALESCE(local.num_quantity, 0)) = 0, global.cost_per_denom, ((local.denom_cost - COALESCE(local.num_cost, 0)) / (local.denom_quantity - COALESCE(local.num_quantity, 0))))
        )
     ) AS cost_savings_90,
  local.*
FROM
  {measures}.regtm_data_{measure_id} AS local
LEFT JOIN
  {measures}.global_data_{measure_id} global
ON
  (global.month = local.month)
