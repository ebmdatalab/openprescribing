cp Technical_Specification_of_data_files_R2_v3.1_May_2015.csv schema_very_raw.csv
gsed -i '0,/^Appendix A/d' schema_very_raw.csv
gsed -i '/^Appendix B/,$d' schema_very_raw.csv
gsed -i '/CDR018H/d' schema_very_raw.csv 
gsed -i '/^$/d' schema_very_raw.csv 
