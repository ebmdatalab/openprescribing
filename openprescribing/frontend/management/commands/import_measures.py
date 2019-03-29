"""Calculate and store measures based on definitions in
`measure_definitions/` folder.

We use BigQuery to compute measures. This is considerably cheaper than
the alternative, which is looping over thousands of practices
individually with a custom SQL query. However, the tradeoff is that
most of the logic now lives in SQL which is harder to read and test
clearly.
"""

from collections import OrderedDict
from contextlib import contextmanager
import csv
from datetime import datetime
import glob
import json
import logging
import os
import re
import tempfile

from dateutil.relativedelta import relativedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db import transaction

from gcutils.bigquery import Client

from common import utils
from frontend.models import MeasureGlobal, MeasureValue, Measure, ImportLog

from google.api_core.exceptions import BadRequest

logger = logging.getLogger(__name__)

CENTILES = [10, 20, 30, 40, 50, 60, 70, 80, 90]


class Command(BaseCommand):
    '''Supply either --end_date to load data for all months
    up to that date, or --month to load data for just one
    month.

    You can also supply --start_date, or supply a file path that
    includes a timestamp with --month_from_prescribing_filename

    Specify a measure with a single string argument to `--measure`,
    and more than one with a comma-delimited list.

    '''

    def check_definition(self, options, start_date, end_date, verbose):
        """Checks SQL definition for measures.
        """

        # We don't validate JSON here, as this is already done as a
        # side-effect of parsing the command options.
        errors = []
        for measure_id in options['measure_ids']:
            try:
                measure = create_or_update_measure(measure_id, end_date)
                calculation = MeasureCalculation(
                    measure, start_date=start_date, end_date=end_date,
                    verbose=verbose
                )
                calculation.check_definition()
            except BadRequest as e:
                errors.append("* SQL error in `{}`: {}".format(
                    measure_id,
                    e.message))
        if errors:
            raise BadRequest("\n".join(errors))

    def build_measures(self, options, start_date, end_date, verbose):
        with conditional_constraint_and_index_reconstructor(options):
            for measure_id in options['measure_ids']:
                logger.info('Updating measure: %s' % measure_id)
                measure_start = datetime.now()

                with transaction.atomic():
                    measure = create_or_update_measure(measure_id, end_date)

                    if options['definitions_only']:
                        continue

                    calcuation = MeasureCalculation(
                        measure, start_date=start_date, end_date=end_date,
                        verbose=verbose
                    )

                    if not options['bigquery_only']:
                        # Delete any existing measures data older than five years ago.
                        l = ImportLog.objects.latest_in_category('prescribing')
                        five_years_ago = l.current_at - relativedelta(years=5)
                        MeasureValue.objects.filter(month__lte=five_years_ago)\
                                            .filter(measure=measure).delete()
                        MeasureGlobal.objects.filter(month__lte=five_years_ago)\
                                             .filter(measure=measure).delete()

                        # Delete any existing measures data relating to the
                        # current month(s)
                        MeasureValue.objects.filter(month__gte=start_date)\
                                            .filter(month__lte=end_date)\
                                            .filter(measure=measure).delete()
                        MeasureGlobal.objects.filter(month__gte=start_date)\
                                             .filter(month__lte=end_date)\
                                             .filter(measure=measure).delete()

                    # Compute the measures
                    calcuation.calculate(options['bigquery_only'])

                elapsed = datetime.now() - measure_start
                logger.warning("Elapsed time for %s: %s seconds" % (
                    measure_id, elapsed.seconds))

    def handle(self, *args, **options):
        options = self.parse_options(options)
        start = datetime.now()
        start_date = options['start_date']
        end_date = options['end_date']
        verbose = options['verbosity'] > 1
        if options['check']:
            action = self.check_definition
        else:
            action = self.build_measures
        action(options, start_date, end_date, verbose)
        logger.warning("Total elapsed time: %s" % (
            datetime.now() - start))

    def add_arguments(self, parser):
        parser.add_argument('--month')
        parser.add_argument('--start_date')
        parser.add_argument('--end_date')
        parser.add_argument('--measure')
        parser.add_argument('--definitions_only', action='store_true')
        parser.add_argument('--bigquery_only', action='store_true')
        parser.add_argument('--check', action='store_true')

    def parse_options(self, options):
        """Parse command line options
        """
        if bool(options['start_date']) != bool(options['end_date']):
            raise CommandError(
                '--start_date and --end_date must be given together')

        if options['measure']:
            options['measure_ids'] = options['measure'].split(',')
        else:
            options['measure_ids'] = [
                k for k, v in parse_measures().items() if 'skip' not in v]

        if not options['start_date']:
            if options['month']:
                options['start_date'] = options['end_date'] = options['month']
            else:
                l = ImportLog.objects.latest_in_category('prescribing')
                start_date = l.current_at - relativedelta(years=5)
                options['start_date'] = start_date.strftime('%Y-%m-%d')
                options['end_date'] = l.current_at.strftime('%Y-%m-%d')
        # validate the date format
        datetime.strptime(options['start_date'], "%Y-%m-%d")
        datetime.strptime(options['end_date'], "%Y-%m-%d")
        return options


def get_measure_definition_paths():
    fpath = os.path.dirname(__file__)
    return sorted(glob.glob(os.path.join(fpath, "./measure_definitions/*.json")))


def parse_measures():
    """Deserialise JSON measures definition into dict
    """
    measures = OrderedDict()
    errors = []

    for path in get_measure_definition_paths():
        measure_id = re.match(r'.*/([^/.]+)\.json', path).groups()[0]
        with open(path) as f:
            try:
                measures[measure_id] = json.load(f)
            except ValueError as e:
                # Add the measure_id to the exception
                errors.append("* {}: {}".format(measure_id, e.message))
    if errors:
        raise ValueError("Problems parsing JSON:\n" + "\n".join(errors))
    return measures


# Utility methods

def float_or_null(v):
    """Return a value coerced to a float, unless it's a None.

    """
    if v is not None:
        v = float(v)
    return v


def float_or_zero(v):
    """Return a value coerced to a float; Nones become zero.
    """
    v = float_or_null(v)
    if v is None:
        v = 0.0
    return v


def convertSavingsToDict(datum, prefix=None):
    """Convert flat list of savings into a dict with centiles as
    keys

    """
    data = {}
    for centile in CENTILES:
        key = "cost_savings_%s" % centile
        if prefix:
            key = "%s_%s" % (prefix, key)
        data[str(centile)] = float_or_zero(datum.pop(key))
    return data


def convertDecilesToDict(datum, prefix=None):
    """Convert flat list of deciles into a dict with centiles as
    keys

    """
    assert prefix
    data = {}
    for centile in CENTILES:
        key = "%s_%sth" % (prefix, centile)
        data[str(centile)] = float_or_null(datum.pop(key))
    return data


def normalisePercentile(percentile):
    """Given a percentile between 0 and 1, or None, return a normalised
    version between 0 and 100, or None.

    """
    percentile = float_or_null(percentile)
    if percentile:
        percentile = percentile * 100
    return percentile


def arrays_to_strings(measure_json):
    """To facilitate readability via newlines, we express some JSON
    strings as arrays, but store them as strings.

    Returns the json with such fields converted to strings.

    """
    fields_to_convert = [
        'title', 'description', 'why_it_matters', 'numerator_columns',
        'numerator_where', 'denominator_columns', 'denominator_where',
        'numerator_bnf_codes_query']

    for field in fields_to_convert:
        if field not in measure_json:
            continue
        if isinstance(measure_json[field], list):
            measure_json[field] = ' '.join(measure_json[field])
    return measure_json


def create_or_update_measure(measure_id, end_date):
    """Create a measure object based on a measure definition

    """
    measure_json = parse_measures()[measure_id]
    v = arrays_to_strings(measure_json)

    try:
        measure = Measure.objects.get(id=measure_id)
    except Measure.DoesNotExist:
        measure = Measure(id=measure_id)

    measure.title = v['title']
    measure.description = v['description']
    measure.why_it_matters = v['why_it_matters']
    measure.name = v['name']
    measure.tags = v['tags']
    measure.tags_focus = v.get('tags_focus', [])
    measure.title = v['title']
    measure.description = v['description']
    measure.numerator_short = v['numerator_short']
    measure.denominator_short = v['denominator_short']
    measure.numerator_from = v['numerator_from']
    measure.numerator_where = v['numerator_where']
    measure.numerator_columns = v['numerator_columns']
    measure.denominator_from = v['denominator_from']
    measure.denominator_where = v['denominator_where']
    measure.denominator_columns = v['denominator_columns']
    measure.url = v['url']
    measure.is_cost_based = v['is_cost_based']
    measure.is_percentage = v['is_percentage']
    measure.low_is_good = v['low_is_good']
    measure.numerator_bnf_codes_query = v.get('numerator_bnf_codes_query')
    measure.numerator_is_list_of_bnf_codes = v.get('numerator_is_list_of_bnf_codes', True)
    measure.numerator_bnf_codes = get_numerator_bnf_codes(measure, end_date)
    measure.save()

    return measure


def get_numerator_bnf_codes(measure, end_date):
    # For most measures, we are able to work out which presentations contribute
    # to variation in the numerator by constructing a query using the
    # numerator_from and numerator_where attributes of the measure.  In a
    # handful of cases this cannot be done, and the creator of the measure must
    # provide a query (numerator_bnf_codes_query) that can be used for this.
    #
    # For the lpzomnibus query, numerator_bnf_codes_query was produced with
    # help from:
    #
    # >>> for m in Measure.objects.filter(tags__contains=['lowpriority']):
    # ...   print '"' + m.numerator_where.strip() + ' OR",'

    if not measure.numerator_is_list_of_bnf_codes:
        return []

    if measure.numerator_bnf_codes_query is not None:
        sql = measure.numerator_bnf_codes_query
        three_months_ago = (
            datetime.strptime(end_date, '%Y-%m-%d') - relativedelta(months=2)
        )
        substitutions = {
            'three_months_ago': three_months_ago.strftime('%Y-%m-01 00:00:00')
        }

    else:
        # It would be nice if we could do:
        #
        #     SELECT normalised_prescribing_standard.bnf_code FROM ...
        #
        # but BQ doesn't let you refer to an aliased table by its original
        # name, so we have to mess around like this.
        if '{hscic}.normalised_prescribing_standard p' in measure.numerator_from:
            col_name = 'p.bnf_code'
        else:
            col_name = 'bnf_code'

        sql = '''
        SELECT DISTINCT {col_name}
        FROM {numerator_from}
        WHERE {numerator_where}
        ORDER BY bnf_code
        '''.format(
            col_name=col_name,
            numerator_from=measure.numerator_from,
            numerator_where=measure.numerator_where,
        )
        substitutions = None

    results = Client().query(sql, substitutions=substitutions)
    return [row[0] for row in results.rows]


class MeasureCalculation(object):
    """Logic for measure calculations in BQ."""

    def __init__(self, measure, start_date=None, end_date=None, verbose=False):
        self.verbose = verbose
        self.fpath = os.path.dirname(__file__)
        self.measure = measure
        self.start_date = start_date
        self.end_date = end_date

    def table_name(self, org_type):
        return '{}_data_{}'.format(org_type, self.measure.id)

    def check_definition(self):
        """Check that the measure definition would result in runnable
        practice-level SQL
        """
        self.calculate_practice_ratios(dry_run=True)

    def calculate(self, bigquery_only=False):
        self.calculate_practices(bigquery_only=bigquery_only)
        self.calculate_orgs('ccg', bigquery_only=bigquery_only)
        self.calculate_orgs('stp', bigquery_only=bigquery_only)
        self.calculate_orgs('regtm', bigquery_only=bigquery_only)  # Regional Team
        self.calculate_global(bigquery_only=bigquery_only)

    def calculate_practices(self, bigquery_only=False):
        """Calculate ratios, centiles and (optionally) cost savings at a
        practice level, and write these to the database.

        """
        self.calculate_practice_ratios()
        self.add_practice_percent_rank()
        self.calculate_global_centiles_for_practices()
        if self.measure.is_cost_based:
            self.calculate_cost_savings_for_practices()
        if not bigquery_only:
            self.write_practice_ratios_to_database()

    def calculate_practice_ratios(self, dry_run=False):
        """Given a measure defition, construct a BigQuery query which computes
        numerator/denominator ratios for practices.

        See also comments in SQL.

        """
        m = self.measure
        numerator_aliases = ''
        denominator_aliases = ''
        aliased_numerators = ''
        aliased_denominators = ''
        for col in self._get_col_aliases('denominator'):
            denominator_aliases += ", denom.%s AS denom_%s" % (col, col)
            aliased_denominators += ", denom_%s" % col
        for col in self._get_col_aliases('numerator'):
            numerator_aliases += ", num.%s AS num_%s" % (col, col)
            aliased_numerators += ", num_%s" % col

        context = {
            'numerator_from': m.numerator_from,
            'numerator_where': m.numerator_where,
            'numerator_columns': m.columns_for_select('numerator'),
            'denominator_columns': m.columns_for_select('denominator'),
            'denominator_from': m.denominator_from,
            'denominator_where': m.denominator_where,
            'numerator_aliases': numerator_aliases,
            'denominator_aliases': denominator_aliases,
            'aliased_denominators': aliased_denominators,
            'aliased_numerators': aliased_numerators,
            'start_date': self.start_date,
            'end_date': self.end_date

        }

        self.insert_rows_from_query(
            'practice_ratios',
            self.table_name('practice'),
            context,
            dry_run=dry_run
        )

    def add_practice_percent_rank(self):
        """Add a percentile rank to the ratios table
        """
        self.insert_rows_from_query(
            'practice_percent_rank',
            self.table_name('practice'),
            {}
        )

    def calculate_global_centiles_for_practices(self):
        """Compute overall sums and centiles for each practice."""
        extra_fields = []
        # Add prefixes to the select columns so we can reference the joined
        # tables (bigquery flattens columns names from subqueries using table
        # alias + underscore)
        for col in self._get_col_aliases('numerator'):
            extra_fields.append("num_" + col)
        for col in self._get_col_aliases('denominator'):
            extra_fields.append("denom_" + col)
        extra_select_sql = ""
        for f in extra_fields:
            extra_select_sql += ", SUM(%s) as %s" % (f, f)
        if self.measure.is_cost_based:
            extra_select_sql += (
                ", "
                "(SUM(denom_cost) - SUM(num_cost)) / (SUM(denom_quantity)"
                "- SUM(num_quantity)) AS cost_per_denom,"
                "SUM(num_cost) / SUM(num_quantity) as cost_per_num")

        context = {
            'extra_select_sql': extra_select_sql,
        }

        self.insert_rows_from_query(
            'global_deciles_practices',
            self.table_name('global'),
            context
        )

    def calculate_cost_savings_for_practices(self):
        """Append cost savings column to the Practice working table"""
        self.insert_rows_from_query(
            'practice_cost_savings',
            self.table_name('practice'),
            {}
        )

    def write_practice_ratios_to_database(self):
        """Copy the bigquery ratios data to the local postgres database.

        Uses COPY command via a CSV file for performance as this can
        be a very large number, especially when computing many months'
        data at once.  We drop and then recreate indexes to improve
        load time performance.

        """
        fieldnames = ['regional_team_id', 'stp_id', 'pct_id', 'measure_id', 'num_items', 'numerator',
                      'denominator', 'month',
                      'percentile', 'calc_value', 'denom_items',
                      'denom_quantity', 'denom_cost', 'num_cost',
                      'num_quantity', 'practice_id', 'cost_savings']
        f = tempfile.TemporaryFile(mode='r+')
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        # Write the data we want to load into a file
        for datum in self.get_rows_as_dicts(self.table_name('practice')):
            datum['measure_id'] = self.measure.id
            if self.measure.is_cost_based:
                datum['cost_savings'] = json.dumps(convertSavingsToDict(datum))
            datum['percentile'] = normalisePercentile(datum['percentile'])
            writer.writerow(datum)
        # load data
        copy_str = "COPY frontend_measurevalue(%s) FROM STDIN "
        copy_str += "WITH (FORMAT CSV)"
        self.log(copy_str % ", ".join(fieldnames))
        f.seek(0)
        with connection.cursor() as cursor:
            cursor.copy_expert(copy_str % ", ".join(fieldnames), f)
        f.close()

    def calculate_orgs(self, org_type, bigquery_only=False):
        """Calculate ratios, centiles and (optionally) cost savings at a
        organisation level, and write these to the database.

        """
        self.calculate_org_ratios(org_type)
        self.add_org_percent_rank(org_type)
        self.calculate_global_centiles_for_orgs(org_type)
        if self.measure.is_cost_based:
            self.calculate_cost_savings_for_orgs(org_type)
        if not bigquery_only:
            self.write_org_ratios_to_database(org_type)

    def calculate_org_ratios(self, org_type):
        """Sums all the fields in the per-practice table, grouped by
        organisation. Stores in a new table.

        """
        numerator_aliases = denominator_aliases = ''
        for col in self._get_col_aliases('denominator'):
            denominator_aliases += ", SUM(denom_%s) AS denom_%s" % (
                col, col)
        for col in self._get_col_aliases('numerator'):
            numerator_aliases += ", SUM(num_%s) AS num_%s" % (col, col)

        context = {
            'denominator_aliases': denominator_aliases,
            'numerator_aliases': numerator_aliases,
        }
        self.insert_rows_from_query(
            '{}_ratios'.format(org_type),
            self.table_name(org_type),
            context
        )

    def add_org_percent_rank(self, org_type):
        """Add a percentile rank to the ratios table
        """
        self.insert_rows_from_query(
            '{}_percent_rank'.format(org_type),
            self.table_name(org_type),
            {}
        )

    def calculate_global_centiles_for_orgs(self, org_type):
        """Adds centiles to the already-existing centiles table
        """
        extra_fields = []
        # Add prefixes to the select columns so we can reference the joined
        # tables (bigquery flattens columns names from subqueries using table
        # alias + underscore)
        for col in self._get_col_aliases('numerator'):
            extra_fields.append("num_" + col)
        for col in self._get_col_aliases('denominator'):
            extra_fields.append("denom_" + col)
        extra_select_sql = ""
        for f in extra_fields:
            extra_select_sql += ", global_deciles.%s as %s" % (f, f)
        if self.measure.is_cost_based:
            extra_select_sql += (
                ", global_deciles.cost_per_denom AS cost_per_denom"
                ", global_deciles.cost_per_num AS cost_per_num")

        context = {
            'extra_select_sql': extra_select_sql,
        }

        self.insert_rows_from_query(
            'global_deciles_{}s'.format(org_type),
            self.table_name('global'),
            context
        )

    def calculate_cost_savings_for_orgs(self, org_type):
        """Appends cost savings column to the organisation ratios table"""
        self.insert_rows_from_query(
            '{}_cost_savings'.format(org_type),
            self.table_name(org_type),
            {}
        )

    def write_org_ratios_to_database(self, org_type):
        """Create measure values for organisation ratios.
        """
        for datum in self.get_rows_as_dicts(self.table_name(org_type)):
            datum['measure_id'] = self.measure.id
            if self.measure.is_cost_based:
                datum['cost_savings'] = convertSavingsToDict(datum)
            datum['percentile'] = normalisePercentile(datum['percentile'])
            MeasureValue.objects.create(**datum)

    def calculate_global(self, bigquery_only=False):
        if self.measure.is_cost_based:
            self.calculate_global_cost_savings()
        if not bigquery_only:
            self.write_global_centiles_to_database()

    def calculate_global_cost_savings(self):
        """Sum cost savings at practice and CCG levels.

        Reads from the existing global table and writes back to it again.
        """
        self.insert_rows_from_query(
            'global_cost_savings',
            self.table_name('global'),
            {}
        )

    def write_global_centiles_to_database(self):
        """Write the globals data from BigQuery to the local database
        """
        self.log("Writing global centiles from %s to database"
                 % self.table_name('global'))
        for d in self.get_rows_as_dicts(self.table_name('global')):
            regtm_cost_savings = {}
            stp_cost_savings = {}
            ccg_cost_savings = {}
            practice_cost_savings = {}
            d['measure_id'] = self.measure.id
            # The cost-savings calculations prepend columns with
            # global_. There is probably a better way of contstructing
            # the query so this clean-up doesn't have to happen...
            new_d = {}
            for attr, value in d.iteritems():
                new_d[attr.replace('global_', '')] = value
            d = new_d

            mg, _ = MeasureGlobal.objects.get_or_create(
                measure_id=self.measure.id,
                month=d['month']
            )

            # Coerce decile-based values into JSON objects
            if self.measure.is_cost_based:
                practice_cost_savings = convertSavingsToDict(
                    d, prefix='practice')
                ccg_cost_savings = convertSavingsToDict(
                    d, prefix='ccg')
                stp_cost_savings = convertSavingsToDict(
                    d, prefix='stp')
                regtm_cost_savings = convertSavingsToDict(
                    d, prefix='regtm')
                mg.cost_savings = {
                    'regional_team': regtm_cost_savings,
                    'stp': stp_cost_savings,
                    'ccg': ccg_cost_savings,
                    'practice': practice_cost_savings
                }
            practice_deciles = convertDecilesToDict(d, prefix='practice')
            ccg_deciles = convertDecilesToDict(d, prefix='ccg')
            stp_deciles = convertDecilesToDict(d, prefix='stp')
            regtm_deciles = convertDecilesToDict(d, prefix='regtm')
            mg.percentiles = {
                'regional_team': regtm_deciles,
                'stp': stp_deciles,
                'ccg': ccg_deciles,
                'practice': practice_deciles,
            }

            # Set the rest of the data returned from bigquery directly
            # on the model
            for attr, value in d.iteritems():
                setattr(mg, attr, value)
            mg.save()

    def insert_rows_from_query(self, query_id, table_name, ctx, dry_run=False):
        """Interpolate values from ctx into SQL identified by query_id, and
        insert results into given table.
        """
        query_path = os.path.join(self.fpath, 'measure_sql', query_id + '.sql')
        ctx['measure_id'] = self.measure.id

        with open(query_path) as f:
            sql = f.read()

        self.get_table(table_name).insert_rows_from_query(
            sql,
            substitutions=ctx,
            dry_run=dry_run
        )

    def get_rows_as_dicts(self, table_name):
        """Iterate over the specified bigquery table, returning a dict for
        each row of data.

        """
        return self.get_table(table_name).get_rows_as_dicts()

    def get_table(self, table_name):
        client = Client('measures')
        return client.get_table(table_name)

    def log(self, message):
        if self.verbose:
            logger.warning(message)
        else:
            logger.info(message)

    def _get_col_aliases(self, num_or_denom=None):
        """Return column names referred to in measure definitions for both
        numerator or denominator.

        When we use nested SELECTs, we need to know which column names
        have been aliased in the inner SELECT so we can select them
        explicitly by name in the outer SELECT.

        """
        assert num_or_denom in ['numerator', 'denominator']
        cols = []
        cols = self.measure.columns_for_select(num_or_denom=num_or_denom)
        aliases = re.findall(r"AS ([a-z0-9_]+)", cols)
        return [x for x in aliases if x not in num_or_denom]


@contextmanager
def conditional_constraint_and_index_reconstructor(options):
    if options['measure']:
        # This is an optimisation that only makes sense when we're
        # updating the entire table.
        yield
    else:
        with utils.constraint_and_index_reconstructor('frontend_measurevalue'):
            yield
