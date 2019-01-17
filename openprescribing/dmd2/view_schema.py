schema = {
    "vtm": {
        "fields": [
            "nm", 
            "invalid", 
            "abbrevnm", 
            "vtmidprev", 
            "vtmiddt"
        ], 
        "dmd_obj_relations": [
            "vmp"
        ], 
        "other_relations": []
    }, 
    "vmp": {
        "fields": [
            "nm", 
            "vtm", 
            "vpiddt", 
            "vpidprev", 
            "invalid", 
            "abbrevnm", 
            "basis", 
            "nmdt", 
            "nmprev", 
            "basis_prev", 
            "nmchange", 
            "combprod", 
            "pres_stat", 
            "sug_f", 
            "glu_f", 
            "pres_f", 
            "cfc_f", 
            "non_avail", 
            "non_availdt", 
            "df_ind", 
            "udfs", 
            "udfs_uom", 
            "unit_dose_uom"
        ], 
        "dmd_obj_relations": [
            "amp", 
            "vmpp"
        ], 
        "other_relations": [
            "vpi", 
            "ont", 
            "dform", 
            "droute", 
            "control_info"
        ]
    }, 
    "vpi": {
        "fields": [
            "vmp", 
            "ing", 
            "basis_strnt", 
            "bs_subid", 
            "strnt_nmrtr_val", 
            "strnt_nmrtr_uom", 
            "strnt_dnmtr_val", 
            "strnt_dnmtr_uom"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "ont": {
        "fields": [
            "vmp", 
            "form"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "dform": {
        "fields": [
            "vmp", 
            "form"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "droute": {
        "fields": [
            "vmp", 
            "route"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "control_info": {
        "fields": [
            "vmp", 
            "cat", 
            "catdt", 
            "cat_prev"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "amp": {
        "fields": [
            "descr", 
            "vmp", 
            "invalid", 
            "nm", 
            "abbrevnm", 
            "nmdt", 
            "nm_prev", 
            "supp", 
            "lic_auth", 
            "lic_auth_prev", 
            "lic_authchange", 
            "lic_authchangedt", 
            "combprod", 
            "flavour", 
            "ema", 
            "parallel_import", 
            "avail_restrict"
        ], 
        "dmd_obj_relations": [
            "ampp"
        ], 
        "other_relations": [
            "ap_ing", 
            "lic_route", 
            "ap_info"
        ]
    }, 
    "ap_ing": {
        "fields": [
            "amp", 
            "ing", 
            "strnth", 
            "uom"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "lic_route": {
        "fields": [
            "amp", 
            "route"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "ap_info": {
        "fields": [
            "amp", 
            "sz_weight", 
            "colour", 
            "prod_order_no"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "vmpp": {
        "fields": [
            "nm", 
            "vmp", 
            "invalid", 
            "qtyval", 
            "qty_uom", 
            "combpack"
        ], 
        "dmd_obj_relations": [
            "ampp"
        ], 
        "other_relations": [
            "dtinfo"
        ]
    }, 
    "dtinfo": {
        "fields": [
            "vmpp", 
            "pay_cat", 
            "price", 
            "dt", 
            "prevprice"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "ampp": {
        "fields": [
            "nm", 
            "vmpp", 
            "amp", 
            "invalid", 
            "abbrevnm", 
            "combpack", 
            "legal_cat", 
            "subp", 
            "disc", 
            "discdt"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": [
            "pack_info", 
            "prescrib_info", 
            "price_info", 
            "reimb_info", 
            "gtin"
        ]
    }, 
    "pack_info": {
        "fields": [
            "ampp", 
            "reimb_stat", 
            "reimb_statdt", 
            "reimb_statprev", 
            "pack_order_no"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "prescrib_info": {
        "fields": [
            "ampp", 
            "sched_2", 
            "acbs", 
            "padm", 
            "fp10_mda", 
            "sched_1", 
            "hosp", 
            "nurse_f", 
            "enurse_f", 
            "dent_f"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "price_info": {
        "fields": [
            "ampp", 
            "price", 
            "pricedt", 
            "price_prev", 
            "price_basis"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "reimb_info": {
        "fields": [
            "ampp", 
            "px_chrgs", 
            "disp_fees", 
            "bb", 
            "cal_pack", 
            "spec_cont", 
            "dnd", 
            "fp34d"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "ing": {
        "fields": [
            "isiddt", 
            "isidprev", 
            "invalid", 
            "nm"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "combination_pack_ind": {
        "fields": [
            "cd", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "combination_prod_ind": {
        "fields": [
            "cd", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "basis_of_name": {
        "fields": [
            "cd", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "namechange_reason": {
        "fields": [
            "cd", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "virtual_product_pres_status": {
        "fields": [
            "cd", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "control_drug_category": {
        "fields": [
            "cd", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "licensing_authority": {
        "fields": [
            "cd", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "unit_of_measure": {
        "fields": [
            "cd", 
            "cddt", 
            "cdprev", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "form": {
        "fields": [
            "cd", 
            "cddt", 
            "cdprev", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "ont_form_route": {
        "fields": [
            "cd", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "route": {
        "fields": [
            "cd", 
            "cddt", 
            "cdprev", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "dt_payment_category": {
        "fields": [
            "cd", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "supplier": {
        "fields": [
            "cd", 
            "cddt", 
            "cdprev", 
            "invalid", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "flavour": {
        "fields": [
            "cd", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "colour": {
        "fields": [
            "cd", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "basis_of_strnth": {
        "fields": [
            "cd", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "reimbursement_status": {
        "fields": [
            "cd", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "spec_cont": {
        "fields": [
            "cd", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "dnd": {
        "fields": [
            "cd", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "virtual_product_non_avail": {
        "fields": [
            "cd", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "discontinued_ind": {
        "fields": [
            "cd", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "df_indicator": {
        "fields": [
            "cd", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "price_basis": {
        "fields": [
            "cd", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "legal_category": {
        "fields": [
            "cd", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "availability_restriction": {
        "fields": [
            "cd", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "licensing_authority_change_reason": {
        "fields": [
            "cd", 
            "descr"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }, 
    "gtin": {
        "fields": [
            "ampp", 
            "gtin", 
            "startdt", 
            "enddt"
        ], 
        "dmd_obj_relations": [], 
        "other_relations": []
    }
}
