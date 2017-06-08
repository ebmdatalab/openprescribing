"""Imports raw XML of dm+d released monthly by NHS BSA.

The dm+d splits items in Virtual Medicinal Products (VMPs) and Actual
Medicinal Products (AMPs; real-world instantiations of particular
idealised medicines).  For example, Paracetamol Capsules might be a
VMP, and the various branded generics of Paracentmol would be AMPs
corresponding to this.

In the legacy BNF model, AMPs and VMPs are mixed together, with AMPs
referring to their corresponding VMP via special coding.

We use table names that match the names in the original XML.  This
allows easier cross-referencing with the Data Model and Implementation
Guides published by the NHS BSA:

 * Data Model: docs/Data_Model_R2_v3.1_May_2015.pdf
 * Implementation: docs/dmd_Implemention_Guide_%28Primary_Care%29_v1.0.pdf

For convenience, and to help match the legacy system to dm+d, it is
convenient to maintain an intermediate entity containing both, which
we call `dmd_product`, in line with the terminology of the NHS BSA's
implementation guide.

That table is created via a series of ordered SQL commands, recorded
in the `dmd_sql/` folder.  Each has a comment at the top with a
reference to relevant page in the Implementation Guide.

We add a `bnf_code` column to that table to facilitate switching
between the legacy BNF system and dm+d. The data in this column is
based on a spreadsheet supplied to us by NHS BSA.

This command therefore expects two sets of data to be supplied in the
folder specified by the `source_directory` argument: dm+d data from
NHS BSA [1], and an Excel spreadsheet currently supplied in private
communication.


[1] https://isd.digital.nhs.uk/trud3/

"""

from lxml import etree
import glob
import os
import re

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db import transaction


PRIMARY_KEYS = {
    'AMP': 'APID',
    'AMPP': 'APPID',
    'VMP': 'VPID',
    'VMPP': 'VPPID'
}

EXTRA_INDEXES = [
    'parallel_import',
    'lic_authcd',
    'pres_statcd',
    'discdt'
]

PG_TYPE_MAP = {
    'xs:date': 'date',
    'xs:string': 'text',
    'xs:integer': 'bigint',
    'xs:float': 'double precision',
}


def create_table(info):
    sql = 'DROP TABLE IF EXISTS "%s"' % info['table_name']
    with connection.cursor() as cursor:
        cursor.execute(sql.lower())
        sql = 'CREATE TABLE "%s" (' % info['table_name']
        cols = []
        indexes = []
        for name, coltype in info['columns']:
            row_sql = '"%s" %s' % (name, coltype)
            if name == PRIMARY_KEYS.get(info['table_name'], ''):
                row_sql += " PRIMARY KEY"
            elif any([name in x
                      for x in PRIMARY_KEYS.values() + EXTRA_INDEXES]):
                indexes.append(name)
            cols.append(row_sql)
        sql += ', '.join(cols)
        sql += ");"
        cursor.execute(sql.lower())
        for i in indexes:
            sql = 'CREATE INDEX IF NOT EXISTS i_%s_%s ON "%s"("%s");' % (
                info['table_name'], i, info['table_name'], i)
            cursor.execute(sql.lower())


def insert_row(cursor, table_info, row_data):
    sql = 'INSERT INTO %s (%s) VALUES (%s)'
    table_name = table_info['table_name']
    cols = []
    vals = []
    for col, val in row_data:
        cols.append('"%s"' % col)
        vals.append(val)
    sql = sql % (table_name, ','.join(cols), ','.join(['%s'] * len(vals)))
    cursor.execute(sql.lower(), vals)


def get_table_info(source_directory, schema_names):
    table_prefix = "dmd_"
    # We manually set up GTIN
    all_tables = {}
    for schema_name in schema_names:
        if 'gtin' in schema_name:
            all_tables['dmd_gtin'] = {
                'table_name': 'dmd_gtin',
                'columns': (
                    ('appid', 'bigint'),
                    ('startdt', 'date'),
                    ('enddt', 'date'),
                    ('gtin', 'text'),
                )
            }
            continue
        xmlschema_doc = etree.parse("%s/%s" % (source_directory, schema_name))
        ns = {"xs": "http://www.w3.org/2001/XMLSchema"}
        root = xmlschema_doc.getroot()
        tables = root.findall(
            'xs:element/xs:complexType/xs:sequence/xs:element', ns)
        root_name = root.find('xs:element', ns).attrib['name']
        for table in tables:
            current_table_def = {'root': root_name}
            schema_name = None
            # does it contain references to other bits of schema?
            if len(root.findall('.//xs:all', ns)) > 0:
                current_table_def['long_name'] = table.attrib['name']
                table_metadata = table.find(
                    './xs:complexType/xs:sequence/xs:element', ns)
                schema_name = table_metadata.attrib['type']
                if root_name == 'LOOKUP':
                    # In the LOOKUP namespace, the key we use for
                    # table_name is not unique and is always INFO, so
                    # we special-case that.
                    current_table_def['table_name'] = table_prefix + 'LOOKUP_' + table.attrib['name']
                    current_table_def['node_name'] = "%s/INFO" % table.attrib['name']
                else:
                    current_table_def['table_name'] = table_prefix + table_metadata.attrib['name']
                    current_table_def['node_name'] = table_metadata.attrib['name']

                columns = root.findall(
                    ".//xs:complexType[@name='%s']/xs:all/xs:element" %
                    schema_name, ns)
            else:
                current_table_def['long_name'] = None
                current_table_def['table_name'] = table_prefix + table.attrib['name']
                current_table_def['node_name'] = table.attrib['name']
                columns = table.findall('.//xs:element', ns)
            current_table_def['columns'] = []

            # Add column info to the current table definition
            for column in columns:
                col_name = column.attrib['name']
                col_type = column.attrib['type']
                current_table_def['columns'].append((col_name, PG_TYPE_MAP[col_type]))

            # Now, if it aleady exists having been described elsewhere,
            if current_table_def['table_name'] in all_tables:
                for new_col in current_table_def['columns']:
                    if new_col not in all_tables[current_table_def['table_name']]['columns']:
                        all_tables[current_table_def['table_name']]['columns'].append(new_col)
            else:
                all_tables[current_table_def['table_name']] = current_table_def
    return all_tables


def create_all_tables(source_directory):
    # We have to do them all at once because some schemas are split
    # over multiple files!
    files = [x.split('/')[-1] for x in glob.glob("%s/*xsd" % source_directory)]
    table_info = get_table_info(source_directory, files)
    for name, info in table_info.items():
        create_table(info)


def create_dmd_product():
    # Follow steps from
    # http://www.nhsbsa.nhs.uk/PrescriptionServices/Documents/PrescriptionServices/dmd_Implemention_Guide_(Primary_Care)_v1.0.pdf
    with connection.cursor() as cursor:
        fpath = os.path.dirname(__file__)
        for f in sorted(glob.glob("%s/dmd_sql/*sql" % fpath),
                        key=lambda x: int(re.findall(r'\d+', x)[0])):
            print "Post-processing", f
            with open(f, "rb") as sql:
                sql = sql.read()
                cursor.execute(sql)


def add_bnf_codes(source_directory):
    from openpyxl import load_workbook
    # 113.831 rows in the spreadsheet
    wb = load_workbook(
        filename=os.path.join(
            source_directory, "Converted_DRUG_SNOMED_BNF.xlsx"))
    rows = wb.get_active_sheet().rows
    with connection.cursor() as cursor:
        for row in rows[1:]:  # skip header
            bnf_code = row[0].value
            # atc_code = row[1].value
            snomed_code = row[4].value
            sql = "UPDATE dmd_product SET BNF_CODE = %s WHERE DMDID = %s "
            cursor.execute(sql.lower(), [bnf_code, snomed_code])
            rowcount = cursor.rowcount
            if not rowcount:
                print "When adding BNF codes, could not find", snomed_code


def process_gtin(cursor, f):
    doc = etree.parse(f)
    root = doc.getroot()
    rows = root.findall(".//AMPP")
    table_info = {'table_name': 'dmd_gtin'}
    for row in rows:
        appid = row.find('AMPPID').text
        start_date = row.find('GTINDATA/STARTDT').text
        end_date = row.find('GTINDATA/ENDDT')
        if end_date is not None:
            end_date = end_date.text
        gtin = row.find('GTINDATA/GTIN').text
        row_data = [
            ('appid', appid),
            ('startdt', start_date),
            ('enddt', end_date),
            ('gtin', gtin)
        ]
        insert_row(cursor, table_info, row_data)


def process_datafiles(source_directory):
    create_all_tables(source_directory)
    to_process = glob.glob("%s/*xml" % source_directory)
    with connection.cursor() as cursor:
        for f in to_process:
            print "Processing %s" % f
            if 'gtin' in f:
                process_gtin(cursor, f)
            else:
                doc = etree.parse(f)
                root = doc.getroot()
                ns = ('{http://www.w3.org/2001/XMLSchema-instance}'
                      'noNamespaceSchemaLocation')
                schema = root.attrib[ns]
                table_info = get_table_info(source_directory, [schema])
                for table_name, info in table_info.items():
                    rows = root.findall(".//%s" % info['node_name'])
                    for row in rows:
                        row_data = []
                        for name, col_type in info['columns']:
                            val = row.find(name)
                            if val is not None:
                                val = val.text
                            row_data.append((name, val))
                        insert_row(cursor, info, row_data)


class Command(BaseCommand):
    args = ''
    help = ('Imports dm+d dataset. Download it from '
            'https://isd.digital.nhs.uk/trud3.')

    def add_arguments(self, parser):
        parser.add_argument('--source_directory')

    def handle(self, *args, **options):
        '''
        Import dm+d dataset.
        '''
        if not options['source_directory']:
            raise CommandError('Please supply a source directory')
        with transaction.atomic():
            process_datafiles(options['source_directory'])
        with connection.cursor() as cursor:
            cursor.execute('ANALYZE VERBOSE')
        with transaction.atomic():
            create_dmd_product()
        with transaction.atomic():
            add_bnf_codes(options['source_directory'])
