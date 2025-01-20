-- this sql calculates the ADQ values for benzodiazepines
SELECT
    rx.month AS month, 
    rx.practice AS practice, 
    rx.bnf_name AS bnf_name,
    rx.bnf_code AS bnf_code, 
    SUM(quantity) AS quantity,
    strnt_nmrtr_val, -- strength numerator value from dmd
    strnt_nmrtr_uom, -- strength numerator unit of measurement from dmd
    strnt_dnmtr_val, -- strength denominator value from dmd
    strnt_dnmtr_uom, -- strength numerator unit of measurement from dmd
    adq.adq AS adq_value,
    SUM(quantity) * IEEE_DIVIDE( -- multiplies quantity by normalised adq value to get total usage value
        CASE 
            WHEN strnt_nmrtr_uom = 258685003 THEN strnt_nmrtr_val / 1000 -- divides where uom is in micrograms by 1000 to get milligram value for consistency 
            ELSE strnt_nmrtr_val 
        END, 
        COALESCE(strnt_dnmtr_val, 1) -- divides by unit size value, or 1 if this does not exist
    ) / adq.adq AS strnt_val_mg -- gets adq usage value normalised to mg
FROM 
    hscic.normalised_prescribing AS rx
INNER JOIN 
    dmd.vmp AS vmp
    ON CONCAT(SUBSTR(rx.bnf_code, 0, 9), SUBSTR(rx.bnf_code, -2)) = CONCAT(SUBSTR(vmp.bnf_code, 0, 9), SUBSTR(vmp.bnf_code, -2)) --joins "generic" BNF code to dm+d
INNER JOIN 
    dmd.vpi AS vpi
    ON vpi.vmp = vmp.id -- joins from vmp to vpi (where strengths are stored)
INNER JOIN 
    measures.adq_bdz AS adq --joins to bdz ADQ table
    ON SUBSTR(rx.bnf_code, 0, 9) = adq.chemical_code
WHERE 
    rx.bnf_code LIKE '0401%' AND -- Hypnotics and Anxiolytics
    rx.bnf_code NOT LIKE '0401010S0%' AND -- Potassium bromide
    rx.bnf_code NOT LIKE '0401010AC%' AND -- Sodium Oxybate
    rx.bnf_code NOT LIKE '0401010AD%' AND -- Melatonin
    rx.bnf_code NOT LIKE '0401040%' AND -- Other hypnotics and anxiolytics
    rx.bnf_code NOT LIKE '0401020K0%AD' AND -- Diazepam_Soln 5mg/2.5ml Rectal Tube
    rx.bnf_code NOT LIKE '0401020K0%AE' AND -- Diazepam_Soln 10mg/2.5ml Rectal Tube
    rx.bnf_code NOT LIKE '0401020K0%BQ' -- Diazepam_Soln 2.5mg/1.25ml Rectal Tube
GROUP BY 
    month, 
    rx.bnf_name, 
    rx.bnf_code, 
    rx.practice,
    strnt_nmrtr_val, 
    strnt_nmrtr_uom, 
    strnt_dnmtr_val, 
    strnt_dnmtr_uom,
    adq.adq
