SELECT
    prescribing.practice AS practice_id,
    CAST(prescribing.month AS DATE) AS month,
    COALESCE(bnf_map.current_bnf_code, prescribing.bnf_code) AS bnf_code,
    prescribing.items,
    prescribing.quantity,
    CAST(ROUND(100 * prescribing.net_cost) AS INT64) AS net_cost_pence,
    CAST(ROUND(100 * prescribing.actual_cost) AS INT64) AS actual_cost_pence
FROM {hscic}.prescribing_v2 AS prescribing
LEFT JOIN {hscic}.bnf_map
    ON bnf_map.former_bnf_code = prescribing.bnf_code
