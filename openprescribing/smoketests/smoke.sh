# Comma-separate lines, then sum the values in position N.
sum_value() {
   summed=0
   while read -r line ; do
       IFS=',' read -a array <<< "$line"
       summed=$(echo "$summed + ${array[$1]}" | bc)
   done
   echo -n "$summed +"
}

# Generate grep expressions from BNF and org codes.
# TODO: handle empty arrays.
# Remember not to include commas between items in the arrays!
# All generic spending: CHEMICALS=('[A-Z0-9]\{9\}AA[A-Z0-9]\{4\}')
# declare -a CHEMICALS=('0212000B0' '0212000C0' '0212000M0' '0212000X0' '0212000Y0')
declare -a CHEMICALS=('0304')
declare -a ORGS=('A81015')
CHEM_STR=''
for CHEM in "${CHEMICALS[@]}"; do
  CHEM_STR+=",$CHEM\|"
done
ORG_STR=''
for ORG in "${ORGS[@]}"; do
  ORG_STR+=",$ORG,\|"
done
CHEM_STR=${CHEM_STR%??}
ORG_STR=${ORG_STR%??}
# CHEM_STR="'$CHEM_STR'"
# ORG_STR="'$ORG_STR'"
echo 'Looking for chemical string' $CHEM_STR
echo 'Looking for org string' $ORG_STR

# List all data files, or declare them explicitly if you prefer.
cd ./data/raw_data/
# FILES=($(ls -d T201*PDPI+BNFT.CSV))
declare -a FILES=('T201507PDPI+BNFT.CSV') # 'T201502PDPI+BNFT.CSV' 'T201503PDPI+BNFT.CSV')

# Grep for BNF and org codes, then sum the values.
echo 'cost:'
for FILE in "${FILES[@]}"; do
  # echo $CHEM_STR
  # echo $FILE
  # grep $ORG_STR $FILE | sum_value 7
  grep $CHEM_STR $FILE | grep $ORG_STR | sum_value 7
done
echo -e '\nitems:'
for FILE in "${FILES[@]}"; do
  # grep $ORG_STR $FILE | sum_value 5
  grep $CHEM_STR $FILE | grep $ORG_STR | sum_value 5
done
echo -e '\nquantity:'
for FILE in "${FILES[@]}"; do
  grep $CHEM_STR $FILE | grep $ORG_STR | sum_value 8
done

# Grep for BNF and org codes, then sum the values.
# echo 'cost:'
# for FILE in "${FILES[@]}"; do
#   grep $CHEM_STR $FILE | grep $ORG_STR | sum_value 7
#   # if [ "$ORG_STR" == "''" ]; then
#   #   grep $CHEM_STR $FILE | sum_value $POSITION
#   # elif [ "$CHEM_STR" == "''" ]; then
#   #   grep $ORG_STR $FILE | sum_value $POSITION
#   # else
#   # fi
# done
# echo -e '\nitems:'
# for FILE in "${FILES[@]}"; do
#   POSITION=5
#   if [ "$ORG_STR" == "''" ]; then
#     grep $CHEM_STR $FILE | sum_value $POSITION
#   elif [ "$CHEM_STR" == "''" ]; then
#     grep $ORG_STR $FILE | sum_value $POSITION
#   else
#     grep $CHEM_STR $FILE | grep $ORG_STR | sum_value $POSITION
#   fi
# done
# echo -e '\nquantity:'
# for FILE in "${FILES[@]}"; do
#   POSITION=8
#   if [ "$ORG_STR" == "''" ]; then
#     grep $CHEM_STR $FILE | sum_value $POSITION
#   elif [ "$CHEM_STR" == "''" ]; then
#     grep $ORG_STR $FILE | sum_value $POSITION
#   else
#     grep $CHEM_STR $FILE | grep $ORG_STR | sum_value $POSITION
#   fi
# done
