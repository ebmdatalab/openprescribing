# This task generates the fixtures in frontend/tests/fixtures/functional-measures.json.
# The generated data includes Practices and all their parent organisations,
# Measures, MeasureValues, and MeasureGlobals.
#
# There are five Measures:
#
#  * two core
#  * two low-priority
#  * lpzomnibus
#
# The MeasureValues and MeasureGlobals are computed by import_measures.  The
# numerators and denominators are generated randomly, such that:
#
#  * the ratios decline over time
#  * the ratios increase with practice ID
#  * the numerators are more expensive than non-numerators
#
# The first two points aren't currently important for the tests (they just
# produce nice charts) but the last point is important, since the cost-saving
# calculations assume this.

from __future__ import print_function

import csv
import json
import os
import tempfile
from random import randint

from django.conf import settings
from django.core.management import BaseCommand, call_command

from frontend import bq_schemas as schemas
from frontend.models import ImportLog, Measure, MeasureGlobal, MeasureValue, Practice, PCT, STP, RegionalTeam
from gcutils.bigquery import Client


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # Ensure that we'll use the test BQ instance
        assert settings.BQ_PROJECT == 'ebmdatalabtest', settings.BQ_PROJECT

        # Ensure we won't pick up any unexpected models
        for model in [Measure, MeasureGlobal, MeasureValue, Practice, PCT, STP, RegionalTeam]:
            assert model.objects.count() == 0, model

        # Delete any ImportLogs that were created by migrations
        ImportLog.objects.all().delete()

        # Create a bunch of RegionalTeams, STPs, CCGs, Practices
        for regtm_ix in range(2):
            regtm = RegionalTeam.objects.create(
                code='Y0{}'.format(regtm_ix),
                name='Region {}'.format(regtm_ix),
            )

            for stp_ix in range(2):
                stp = STP.objects.create(
                    ons_code='E000000{}{}'.format(regtm_ix, stp_ix),
                    name='STP {}/{}'.format(regtm_ix, stp_ix),
                )

                for ccg_ix in range(2):
                    ccg = PCT.objects.create(
                        regional_team=regtm,
                        stp=stp,
                        code='{}{}{}'.format(regtm_ix, stp_ix, ccg_ix).replace('0', 'A'),
                        name='CCG {}/{}/{}'.format(regtm_ix, stp_ix, ccg_ix),
                        org_type='CCG',
                    )

                    for prac_ix in range(2):
                        Practice.objects.create(
                            ccg=ccg,
                            code='P0{}{}{}{}'.format(regtm_ix, stp_ix, ccg_ix, prac_ix),
                            name='Practice {}/{}/{}/{}'.format(regtm_ix, stp_ix, ccg_ix, prac_ix),
                            setting=4,
                            address1='',
                            address2='',
                            address3='',
                            address4='',
                            address5='',
                            postcode='',
                        )

        # import_measures uses this ImportLog to work out which months it
        # should import data.
        ImportLog.objects.create(
            category='prescribing',
            current_at='2018-08-01',
        )

        # Practice and CCG homepages need this to work out which PPU savings to
        # show.
        ImportLog.objects.create(
            category='ppu',
            current_at='2018-08-01',
        )

        # Set up BQ, and upload STPs, CCGs, Practices.
        Client('measures').create_dataset()
        client = Client('hscic')
        table = client.get_or_create_table('ccgs', schemas.CCG_SCHEMA)
        columns = [field.name for field in schemas.CCG_SCHEMA]
        table.insert_rows_from_pg(PCT, columns, schemas.ccgs_transform)
        table = client.get_or_create_table('practices', schemas.PRACTICE_SCHEMA)
        columns = [field.name for field in schemas.PRACTICE_SCHEMA]
        table.insert_rows_from_pg(Practice, columns)

        # Create measures definitions and record the BNF codes used
        measure_definitions_path = os.path.join(
            settings.APPS_ROOT,
            'frontend',
            'management',
            'commands',
            'measure_definitions'
        )

        # lpzomnibus is a real measure, and we don't want to overwrite its
        # definition.
        os.rename(
            os.path.join(measure_definitions_path, 'lpzomnibus.json'),
            os.path.join(measure_definitions_path, 'lpzomnibus.json.bak'),
        )

        bnf_codes = []

        for ix in range(5):
            numerator_where = "bnf_code LIKE '0{}01%'".format(ix),
            denominator_where = "bnf_code LIKE '0{}%'".format(ix),

            if ix in [0, 1]:
                measure_id = 'core_{}'.format(ix)
                name = 'Core measure {}'.format(ix)
                tags = ['core']
                tags_focus = None
            elif ix in [2, 3]:
                measure_id = 'lp_{}'.format(ix)
                name = 'LP measure {}'.format(ix)
                tags = ['lowpriority']
                tags_focus = None
            else:
                assert ix == 4
                measure_id = 'lpzomnibus'
                name = 'LP omnibus measure'
                tags = ['core']
                tags_focus = ['lowpriority']
                numerator_where = "bnf_code LIKE '0201%' OR bnf_code LIKE'0301%'",
                denominator_where = "bnf_code LIKE '02%' OR bnf_code LIKE'03%'",

            measure_definition = {
                'name': name,
                'title': '{} Title'.format(ix),
                'description': '{} description'.format(name),
                'why_it_matters': 'Why {} matters'.format(name),
                'url': 'http://example.com/measure-{}'.format(measure_id),
                'numerator_short': 'Numerator for {}'.format(measure_id),
                'numerator_from': '{hscic}.normalised_prescribing_standard',
                'numerator_where': numerator_where,
                'numerator_columns': 'SUM(quantity) AS numerator',
                'denominator_short': 'Denominator for {}'.format(measure_id),
                'denominator_from': '{hscic}.normalised_prescribing_standard',
                'denominator_where': denominator_where,
                'denominator_columns': 'SUM(quantity) AS denominator',
                'is_cost_based': True,
                'is_percentage': True,
                'low_is_good': True,
                'tags': tags,
                'tags_focus': tags_focus,
            }

            path = os.path.join(
                measure_definitions_path,
                '{}.json'.format(measure_id)
            )
            with open(path, 'w') as f:
                json.dump(measure_definition, f, indent=2)

            bnf_codes.append('0{}0000000000000'.format(ix))
            bnf_codes.append('0{}0100000000000'.format(ix))

        # Generate random prescribing data.  This data is never saved to the
        # database.
        prescribing_rows = []

        for practice_ix, practice in enumerate(Practice.objects.all()):
            for month in [1, 2, 3, 4, 5, 6, 7, 8]:
                timestamp = '2018-0{}-01 00:00:00 UTC'.format(month)

                # 0 <= practice_ix <= 15; 1 <= month <= 8
                item_ratio = (22 + practice_ix - 2 * month + randint(-5, 5)) / 43.0
                assert 0 < item_ratio < 1

                numerator_items = 100 + randint(0, 100)
                denominator_items = int(numerator_items / item_ratio)

                for bnf_code_ix, bnf_code in enumerate(bnf_codes):
                    if bnf_code_ix % 2 == 0:
                        items = denominator_items
                    else:
                        items = numerator_items

                    quantity = 28 * items
                    unit_cost = 1 + bnf_code_ix
                    actual_cost = unit_cost * quantity

                    # We don't care about net_cost.
                    net_cost = actual_cost

                    row = [
                        'sha',  # This value doesn't matter.
                        practice.ccg.regional_team_id,
                        practice.ccg.stp_id,
                        practice.ccg_id,
                        practice.code,
                        bnf_code,
                        'bnf_name',  # This value doesn't matter
                        items,
                        net_cost,
                        actual_cost,
                        quantity,
                        timestamp,
                    ]

                    prescribing_rows.append(row)

        # In production, normalised_prescribing_standard is actually a view,
        # but for the tests it's much easier to set it up as a normal table.
        table = client.get_or_create_table(
            'normalised_prescribing_standard',
            schemas.PRESCRIBING_SCHEMA
        )

        # Upload prescribing_rows to normalised_prescribing_standard.
        with tempfile.NamedTemporaryFile() as f:
            writer = csv.writer(f)
            for row in prescribing_rows:
                writer.writerow(row)
            f.seek(0)
            table.insert_rows_from_csv(f.name)

        # Do the work.
        call_command('import_measures', measure='core_0,core_1,lp_2,lp_3,lpzomnibus')

        # Clean up.
        for ix in range(5):
            numerator_where = "bnf_code LIKE '0{}01%'".format(ix),
            denominator_where = "bnf_code LIKE '0{}%'".format(ix),

            if ix in [0, 1]:
                measure_id = 'core_{}'.format(ix)
            elif ix in [2, 3]:
                measure_id = 'lp_{}'.format(ix)
            else:
                assert ix == 4
                measure_id = 'lpzomnibus'

            path = os.path.join(
                measure_definitions_path,
                '{}.json'.format(measure_id)
            )
            os.remove(path)

        os.rename(
            os.path.join(measure_definitions_path, 'lpzomnibus.json.bak'),
            os.path.join(measure_definitions_path, 'lpzomnibus.json'),
        )

        # Dump the fixtures.
        fixture_path = os.path.join('frontend', 'tests', 'fixtures', 'functional-measures.json')
        call_command(
            'dumpdata',
            'frontend',
            indent=2,
            output=fixture_path
        )
