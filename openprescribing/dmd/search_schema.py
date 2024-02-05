# Fields that are commented out below are too complicated for QueryBuilder.

schema = {
    "vmp": {
        "fields": [
            "nm",
            "bnf_code",
            "vpiddt",
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
            "unit_dose_uom",
            "ont",
            "dform",
            "droute",
            "controlinfo",
            # "vpi",
        ]
    },
    "amp": {
        "fields": [
            "descr",
            "nm",
            "bnf_code",
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
            "avail_restrict",
            # "aping",
            "licroute",
            # "apinfo",
        ]
    },
    "vmpp": {
        "fields": [
            "nm",
            "bnf_code",
            "qtyval",
            "qty_uom",
            "combpack",
            # "dtinfo",
        ]
    },
    "ampp": {
        "fields": [
            "nm",
            "bnf_code",
            "abbrevnm",
            "combpack",
            "legal_cat",
            "subp",
            "disc",
            "discdt",
            # "pack_info",
            # "prescrib_info",
            # "price_info",
            # "reimb_info",
            # "gtin",
        ]
    },
}
