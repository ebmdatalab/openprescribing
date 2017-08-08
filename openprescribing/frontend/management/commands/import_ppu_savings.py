from sets import Set
import os

import pandas as pd

from django.core.management.base import BaseCommand
from django.db import transaction

from ebmdatalab.bigquery import query_and_return

from common.utils import valid_date
from dmd.models import DMDProduct
from frontend.models import ImportLog
from frontend.models import PPUSaving
from frontend.models import Presentation


def gbq_sql_to_dataframe(sql):
    """Return results of BigQuery SQL as a DataFrame.

    If there's an error, prints the SQL with line numbers before
    re-raising.

    """
    try:
        df = pd.io.gbq.read_gbq(
            sql,
            project_id="ebmdatalab",
            verbose=False,
            dialect='legacy',
            private_key=os.environ['GOOGLE_APPLICATION_CREDENTIALS'])
        return df
    except:
        for n, line in enumerate(sql.split("\n")):
            print "%s: %s" % (n+1, line)
        raise


def make_merged_table_for_month(
        substitutions_csv='',
        month='',
        namespace='hscic'):
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
    df = pd.read_csv(substitutions_csv)
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
    query = """
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
        ebmdatalab.%s.%s
      WHERE month = TIMESTAMP('%s')
    """ % (' '.join(
        ["WHEN '%s' THEN '%s'" % (when_code, then_code)
         for (when_code, then_code) in cases]),
           namespace,
           prescribing_table,
           month)
    target_table_name = (
        'prescribing_with_merged_codes_%s' % month.strftime('%Y_%m'))
    query_and_return('ebmdatalab', namespace,
                     target_table_name,
                     query, legacy=False)
    return target_table_name


def get_savings(for_entity='', group_by='', month='', cost_field='net_cost',
                sql_only=False, limit=1000, order_by_savings=True,
                min_saving=0, namespace='hscic', substitutions_csv=''):
    """Execute SQL to calculate savings in BigQuery, and return as a
    DataFrame.

    References to issues below are for
    https://github.com/ebmdatalab/price-per-dose/issues

    """
    assert month
    assert group_by or for_entity
    assert group_by in ['', 'pct', 'practice', 'product']

    prescribing_table = "ebmdatalab.%s.%s" % (
        namespace,
        make_merged_table_for_month(
            substitutions_csv=substitutions_csv,
            month=month,
            namespace=namespace)
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
    if len(for_entity) == 3:
        restricting_condition += 'AND pct = "%s"' % for_entity
        group_by = 'pct'
    elif len(for_entity) > 3:
        restricting_condition += 'AND practice = "%s"' % for_entity
        group_by = 'practice'
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

    if limit:
        limit = "LIMIT %s" % limit
    else:
        limit = ''

    if order_by_savings:
        order_by = "ORDER BY possible_savings DESC"
    else:
        order_by = ''
    fpath = os.path.dirname(__file__)

    # Execute SQL
    with open("%s/ppu_sql/savings_for_decile.sql" % fpath, "r") as f:
        sql = f.read()
        substitutions = (
            ('{{ restricting_condition }}', restricting_condition),
            ('{{ limit }}', limit),
            ('{{ month }}', month.strftime('%Y-%m-%d')),
            ('{{ group_by }}', group_by),
            ('{{ order_by }}', order_by),
            ('{{ select }}', select),
            ('{{ prescribing_table }}', prescribing_table),
            ('{{ cost_field }}', cost_field),
            ('{{ inner_select }}', inner_select),
            ('{{ min_saving }}', min_saving)
        )
        for key, value in substitutions:
            sql = sql.replace(key, str(value))
        if sql_only:
            return sql
        else:
            # Format results in a DataFrame
            df = gbq_sql_to_dataframe(sql)
            # Rename null values in category, so we can group by it
            df.loc[df['category'].isnull(), 'category'] = 'NP8'
            df = df.set_index(
                'generic_presentation')
            df.index.name = 'bnf_code'
            # Add in substitutions column
            subs = pd.read_csv(substitutions_csv).set_index('Code')
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
            type=valid_date, required=True)
        parser.add_argument(
            '--min-practice-saving',
            type=int, default=50)
        parser.add_argument(
            '--substitutions-csv',
            help='Path to CSV detailing Tab/Cap substitutions etc',
            type=str, required=True)
        parser.add_argument(
            '--min-ccg-saving',
            help="Disregard savings under this amount",
            type=int, default=1000)
        parser.add_argument(
            '--limit',
            help="Maximum number of savings to return",
            type=int, default=0)

    def handle(self, *args, **options):
        '''
        Compute and store cost savings for the specified month.

        Deletes any existing data for that month.
        '''
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
                is_generic=False)
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
                is_generic=False)
            PPUSaving.objects.filter(date=options['month']).delete()
            for entity_type, min_saving in [
                    ('pct', options['min_ccg_saving']),
                    ('practice', options['min_practice_saving'])]:
                result = get_savings(
                    group_by=entity_type,
                    month=options['month'],
                    limit=options['limit'],
                    min_saving=min_saving,
                    substitutions_csv=options['substitutions_csv'])
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
