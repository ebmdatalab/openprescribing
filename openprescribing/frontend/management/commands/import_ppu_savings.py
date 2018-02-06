from sets import Set
import argparse
import os

import pandas as pd

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from gcutils.bigquery import Client

from common.utils import valid_date
from dmd.models import DMDProduct
from frontend.models import ImportLog
from frontend.models import PPUSaving
from frontend.models import Presentation

SUBSTITUTIONS_SPREADSHEET = (
    'https://docs.google.com/spreadsheets/d/e/'
    '2PACX-1vSsTrjEdRekkcR0H8myL8RwP3XKg2YvTgQwGb5ypNei0IYn4ofr'
    'ayVZJibLfN_lnpm6Q9qu_t0yXU5Z/pub?gid=1784930737&single=true'
    '&output=csv')


def make_merged_table_for_month(month):
    """Create a new BigQuery table that includes code substitutions, off
    which our savings can be computed.

    What are code substitutions?

    Because (for example) Tramadol tablets and capsules can
    almost always be substituted, we consider them the same chemical
    for the purposes of our analysis.

    Therefore, wherever Tramadol capsules appear in the source data,
    we treat them as Tramadol tablets (for example).

    The mapping of what we consider equivalent is stored in a Google
    Sheet, currently at
    https://docs.google.com/spreadsheets/d/1SvMGCKrmqsNkZYuGW18Sf0wTluXyV4bhyZQaVLcO41c/edit

    The process of updating this spreadsheet (which should be done
    periodically) is documented
    [here](https://github.com/ebmdatalab/price-per-dose/issues/11)

    """
    cases = []
    seen = Set()
    df = pd.read_csv(SUBSTITUTIONS_SPREADSHEET)
    df = df[df['Really equivalent?'] == 'Y']
    for row in df.iterrows():
        data = row[1]
        source_code = data[1].strip()
        code_to_merge = data[10].strip()
        if source_code not in seen and code_to_merge not in seen:
            cases.append((code_to_merge, source_code))
        seen.add(source_code)
        seen.add(code_to_merge)
    prescribing_table = 'normalised_prescribing_standard'
    sql = """
      SELECT
        practice,
        pct,
      CASE bnf_code
        %s
        ELSE bnf_code
      END AS bnf_code,
        month,
        actual_cost,
        net_cost,
        quantity
      FROM
        {hscic}.%s
      WHERE month = TIMESTAMP('%s')
    """ % (' '.join(
        ["WHEN '%s' THEN '%s'" % (when_code, then_code)
         for (when_code, then_code) in cases]),
           prescribing_table,
           month)
    target_table_name = (
        'prescribing_with_merged_codes_%s' % month.strftime('%Y_%m'))

    client = Client('hscic')
    table = client.get_table(target_table_name)
    table.insert_rows_from_query(sql)
    return target_table_name


def get_savings(group_by, month, min_saving):
    """Execute SQL to calculate savings in BigQuery, and return as a
    DataFrame.

    References to issues below are for
    https://github.com/ebmdatalab/price-per-dose/issues

    """
    prescribing_table = "{hscic}.%s" % (
        make_merged_table_for_month(month)
    )
    restricting_condition = (
        "AND LENGTH(RTRIM(p.bnf_code)) >= 15 "
        "AND p.bnf_code NOT LIKE '0302000C0____BE' "  # issue #10
        "AND p.bnf_code NOT LIKE '0302000C0____BF' "  # issue #10
        "AND p.bnf_code NOT LIKE '0302000C0____BH' "  # issue #10
        "AND p.bnf_code NOT LIKE '0302000C0____BG' "  # issue #10
        "AND p.bnf_code NOT LIKE '0904010H0%' "  # issue #9
        "AND p.bnf_code NOT LIKE '0904010H0%' "  # issue #9
        "AND p.bnf_code NOT LIKE '1311070S0____AA' "  # issue #9
        "AND p.bnf_code NOT LIKE '1311020L0____BS' "  # issue #9
        "AND p.bnf_code NOT LIKE '0301020S0____AA' "  # issue #12
        "AND p.bnf_code NOT LIKE '190700000BBCJA0' "  # issue #12
        "AND p.bnf_code NOT LIKE '0604011L0BGAAAH' "  # issue #12
        "AND p.bnf_code NOT LIKE '1502010J0____BY' "  # issue #12
        "AND p.bnf_code NOT LIKE '1201010F0AAAAAA' "  # issue #12
        "AND p.bnf_code NOT LIKE '0107010S0AAAGAG' "  # issue #12
        "AND p.bnf_code NOT LIKE '060016000BBAAA0' "  # issue #14
        "AND p.bnf_code NOT LIKE '190201000AABJBJ' "  # issue #14
        "AND p.bnf_code NOT LIKE '190201000AABKBK' "  # issue #14
        "AND p.bnf_code NOT LIKE '190201000AABLBL' "  # issue #14
        "AND p.bnf_code NOT LIKE '190201000AABMBM' "  # issue #14
        "AND p.bnf_code NOT LIKE '190201000AABNBN' "  # issue #14
        "AND p.bnf_code NOT LIKE '190202000AAADAD' "  # issue #14
    )

    # Generate variable SQL based on if we're interested in CCG or
    # practice-level data
    if group_by == 'pct':
        select = 'savings.presentations.pct AS pct,'
        inner_select = 'presentations.pct, '
        group_by = 'presentations.pct, '
    elif group_by == 'practice':
        select = ('savings.presentations.practice AS practice,'
                  'savings.presentations.pct AS pct,')
        inner_select = ('presentations.pct, '
                        'presentations.practice,')
        group_by = ('presentations.practice, '
                    'presentations.pct,')
    elif group_by == 'product':
        select = ''
        inner_select = ''
        group_by = ''

    order_by = "ORDER BY possible_savings DESC"
    fpath = os.path.dirname(__file__)

    # Execute SQL
    with open("%s/ppu_sql/savings_for_decile.sql" % fpath, "r") as f:
        sql = f.read()

    substitutions = (
        ('{{ restricting_condition }}', restricting_condition),
        ('{{ month }}', month.strftime('%Y-%m-%d')),
        ('{{ group_by }}', group_by),
        ('{{ order_by }}', order_by),
        ('{{ select }}', select),
        ('{{ prescribing_table }}', prescribing_table),
        ('{{ inner_select }}', inner_select),
        ('{{ min_saving }}', min_saving)
    )
    for key, value in substitutions:
        sql = sql.replace(key, str(value))
    # Format results in a DataFrame
    client = Client()
    df = client.query_into_dataframe(sql, legacy=True)
    # Rename null values in category, so we can group by it
    df.loc[df['category'].isnull(), 'category'] = 'NP8'
    df = df.set_index(
        'generic_presentation')
    df.index.name = 'bnf_code'
    # Add in substitutions column
    subs = pd.read_csv(SUBSTITUTIONS_SPREADSHEET).set_index('Code')
    subs = subs[subs['Really equivalent?'] == 'Y'].copy()
    subs['formulation_swap'] = (
        subs['Formulation'] +
        ' / ' +
        subs['Alternative formulation'])
    df = df.join(
        subs[['formulation_swap']], how='left')
    # Convert nans to Nones
    df = df.where((pd.notnull(df)), None)
    return df


class Command(BaseCommand):
    args = ''
    help = 'Imports cost savings for a month'

    def add_arguments(self, parser):
        parser.add_argument(
            '--month',
            type=valid_date)

    def handle(self, *args, **options):
        '''
        Compute and store cost savings for the specified month.

        Deletes any existing data for that month.
        '''
        if not options['month']:
            last_prescribing = ImportLog.objects.latest_in_category(
                'prescribing').current_at
            options['month'] = last_prescribing

            log = ImportLog.objects.latest_in_category('ppu')
            if log is not None:
                if options['month'] <= log.current_at:
                    raise argparse.ArgumentTypeError("Couldn't infer date")
        with transaction.atomic():
            # Create custom DMD Products for our overrides, if they
            # don't exist.
            DMDProduct.objects.get_or_create(
                dmdid=10000000000,
                bnf_code='0601060D0AAA0A0',
                vpid=10000000000,
                name='Glucose Blood Testing Reagents',
                concept_class=1,
                product_type=1
            )
            Presentation.objects.get_or_create(
                bnf_code='0601060D0AAA0A0',
                name='Glucose Blood Testing Reagents',
                is_generic=True)
            DMDProduct.objects.get_or_create(
                dmdid=10000000001,
                vpid=10000000001,
                bnf_code='0601060U0AAA0A0',
                name='Urine Testing Reagents',
                product_type=1,
                concept_class=1)
            Presentation.objects.get_or_create(
                bnf_code='0601060U0AAA0A0',
                name='Urine Testing Reagents',
                is_generic=True)
            PPUSaving.objects.filter(date=options['month']).delete()
            for entity_type, min_saving in [
                    ('pct', 1000),
                    ('practice', 50)]:
                result = get_savings(entity_type, options['month'], min_saving)
                for row in result.itertuples():
                    d = row._asdict()
                    if d['price_per_unit']:
                        PPUSaving.objects.create(
                            date=options['month'],
                            presentation_id=d['Index'],
                            lowest_decile=d['lowest_decile'],
                            quantity=d['quantity'],
                            price_per_unit=d['price_per_unit'],
                            possible_savings=d['possible_savings'],
                            formulation_swap=d['formulation_swap'] or None,
                            pct_id=d.get('pct', None),
                            practice_id=d.get('practice', None)
                        )
            ImportLog.objects.create(
                category='ppu',
                filename='n/a',
                current_at=options['month'])
