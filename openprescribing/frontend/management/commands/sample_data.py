"""A command to generate or load a subset of data from the live
database.

The `load` operation truncates all existing data.

"""

import json
import os
import tempfile
import subprocess

from django.core.management import BaseCommand
from django.db import connection
from django.template import Context, Engine, Template

# Tables for which we should copy all the data
copy_all = [
    'django_migrations',
    'auth_user',
    'frontend_chemical',
    'frontend_genericcodemapping',
    'frontend_importlog',
    'frontend_measure',
    'frontend_measureglobal',
    'frontend_regionalteam',
    'frontend_stp',
    'frontend_pct',
    'frontend_practice',
    'frontend_orgbookmark',
    'frontend_practiceisdispensing',
    'frontend_presentation',
    'frontend_product',
    'frontend_profile',
    'frontend_qofprevalence',
    'frontend_searchbookmark',
    'frontend_section',
    'pipeline_tasklog',
    'spatial_ref_sys',
    'dmd_lookup_availability_restriction',
    'dmd_lookup_basis_of_name',
    'dmd_lookup_basis_of_strnth',
    'dmd_lookup_colour',
    'dmd_lookup_combination_pack_ind',
    'dmd_lookup_combination_prod_ind',
    'dmd_lookup_control_drug_category',
    'dmd_lookup_df_indicator',
    'dmd_lookup_discontinued_ind',
    'dmd_lookup_dnd',
    'dmd_lookup_dt_payment_category',
    'dmd_lookup_flavour',
    'dmd_lookup_form',
    'dmd_lookup_legal_category',
    'dmd_lookup_licensing_authority',
    'dmd_lookup_licensing_authority_change_reason',
    'dmd_lookup_namechange_reason',
    'dmd_lookup_ont_form_route',
    'dmd_lookup_price_basis',
    'dmd_lookup_reimbursement_status',
    'dmd_lookup_route',
    'dmd_lookup_spec_cont',
    'dmd_lookup_supplier',
    'dmd_lookup_unit_of_measure',
    'dmd_lookup_virtual_product_non_avail',
    'dmd_lookup_virtual_product_pres_status',
    'dmd_amp',
    'dmd_ampp',
    'dmd_ap_info',
    'dmd_ap_ing',
    'dmd_ccontent',
    'dmd_control_info',
    'dmd_dform',
    'dmd_droute',
    'dmd_dtinfo',
    'dmd_gtin',
    'dmd_ing',
    'dmd_lic_route',
    'dmd_ncsoconcession',
    'dmd_ont',
    'dmd_pack_info',
    'dmd_prescrib_info',
    'dmd_price_info',
    'dmd_product',
    'dmd_product_temp',
    'dmd_reimb_info',
    'dmd_tariffprice',
    'dmd_vmp',
    'dmd_vmpp',
    'dmd_vpi',
    'dmd_vtm',
    'vw__practice_summary',
    'vw__presentation_summary',
]

# tables with WHERE clauses
copy_sample = {
    'frontend_measurevalue': "pct_id = '{}'",
    'frontend_prescription': "pct_id = '{}'",
    'frontend_practicestatistics': "pct_id = '{}'",
    'frontend_ppusaving': "pct_id = '{}'",
    'vw__ccgstatistics': "pct_id = '{}'",
    'vw__chemical_summary_by_ccg': "pct_id = '{}'",
    'vw__chemical_summary_by_practice': (
        "practice_id IN "
        "(SELECT code FROM frontend_practice WHERE ccg_id = '{}')"),
    'vw__presentation_summary_by_ccg': "pct_id = '{}'",
}

tables_to_sample = ['frontend_prescription']


def dump_create_table(table, dest_dir):
    """
    Save an array of column names in the order they'll be dumped.

    This allows us to recreate them on loading.
    """
    dest = os.path.join(dest_dir, table + '.json')
    with connection.cursor() as cursor:
        sql = ("SELECT column_name FROM information_schema.columns "
               "WHERE table_schema = 'public' AND table_name = '{}'"
               .format(table))
        res = cursor.execute(sql)
        fields = cursor.fetchall()
        with open(dest, 'wb') as f:
            json.dump([x[0] for x in fields], f)


def quote_cols(cols):
    """Quote SQL column names (because dm+d uses the reserved word `desc`)
    """
    return ['"{}"'.format(item) for item in cols]


class Command(BaseCommand):
    def dump(self, path, ccg):
        with connection.cursor() as cursor:
            for table in copy_all:
                with open(os.path.join(path, table), 'wb') as f:
                    sql = r"copy (SELECT * FROM {}) TO STDOUT WITH NULL '\N'"
                    sql = sql.format(table)
                    dump_create_table(table, path)
                    cursor.copy_expert(sql, f)
            for table, where in copy_sample.items():
                where = where.format(ccg)
                with open(os.path.join(path, table), 'wb') as f:
                    if table in tables_to_sample:
                        sample = 'TABLESAMPLE SYSTEM (1)'
                    else:
                        sample = ''
                    sql = ("copy (SELECT * FROM {} {} WHERE {}) "
                           "TO STDOUT WITH NULL '\N'")
                    sql = sql.format(table, sample, where)
                    dump_create_table(table, path)
                    cursor.copy_expert(sql, f)

    def load(self, path):
        with connection.cursor() as cursor:
            # Create empty views
            view_sql = os.path.join(
                'frontend', 'management', 'commands', 'replace_matviews.sql')
            with open(view_sql, 'rb') as f:
                cursor.execute(f.read())
            # Create DMD tables
            view_sql = os.path.join(
                'dmd', 'dmd_structure.sql')
            with open(view_sql, 'rb') as f:
                cursor.execute(f.read())
            # Now fill other (existing) tables
            for table in copy_all:
                with open(os.path.join(path, table), 'rb') as f:
                    cursor.execute("TRUNCATE TABLE {} CASCADE".format(table))
                    with open(os.path.join(path, table + '.json'), 'rb') as f2:
                        cols = json.load(f2)
                    cursor.copy_from(
                        f, table, null='\N', columns=quote_cols(cols))
            for table, where in copy_sample.items():
                with open(os.path.join(path, table), 'rb') as f:
                    cursor.execute("TRUNCATE TABLE {} CASCADE".format(table))
                    with open(os.path.join(path, table + '.json'), 'rb') as f2:
                        cols = json.load(f2)
                    cursor.copy_from(
                        f, table, null='\N', columns=quote_cols(cols))

    def add_arguments(self, parser):
        parser.add_argument('operation', nargs=1, choices=['load', 'dump'])
        parser.add_argument(
            '--dir',
            help="directory containing previously dumped files",
            default=tempfile.gettempdir())
        parser.add_argument(
            '--ccg', help="CCG to sample data for", default='09X')

    def handle(self, *args, **options):
        if 'load' in options['operation']:
            self.load(options['dir'])
        else:
            self.dump(options['dir'], options['ccg'])
