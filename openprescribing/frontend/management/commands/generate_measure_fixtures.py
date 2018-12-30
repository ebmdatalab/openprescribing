# This task generates the fixtures in frontend/tests/fixtures/functional-measures.json.
# The generated data includes Practices and all their parent organisations,
# Measures, MeasureValues, and MeasureGlobals.  The MeasureValues and
# MeasureGlobals are computed by import_measures.  The numerators and
# denominators are generated randomly, and there is no extra structure,
# although there could be.  For instance, we could make it so that the
# performance of the CCGs follows a certain pattern.

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

        os.rename(
            os.path.join(measure_definitions_path, 'lpzomnibus.json'),
            os.path.join(measure_definitions_path, 'lpzomnibus.json.bak'),
        )

        bnf_codes = []

        for ix in range(3):
            measure_definition = {
                'name': 'Measure {}'.format(ix),
                'title': 'Measure {} Title'.format(ix),
                'description': 'Measure {} description'.format(ix),
                'why_it_matters': 'Why measure {} matters'.format(ix),
                'url': 'http://example.com/measure-{}'.format(ix),
                'numerator_short': 'Numerator {}'.format(ix),
                'numerator_from': '{hscic}.normalised_prescribing_standard',
                'numerator_where': "bnf_code LIKE '0{}01%'".format(ix),
                'numerator_columns': 'SUM(quantity) AS numerator',
                'denominator_short': 'Denominator {}'.format(ix),
                'denominator_from': '{hscic}.normalised_prescribing_standard',
                'denominator_where': "bnf_code LIKE '0{}%'".format(ix),
                'denominator_columns': 'SUM(quantity) AS denominator',
                'is_cost_based': True,
                'is_percentage': True,
                'low_is_good': True,
                'tags': ['core'],
            }

            # lpzomnibus is special-cased in the code
            if ix == 0:
                measure_id = 'lpzomnibus'
            else:
                measure_id = 'measure_{}'.format(ix)

            if ix == 0:
                measure_definition['tags_focus'] = ['lowpriority']

            if ix == 1:
                measure_definition['tags'] = ['lowpriority']

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

        for practice in Practice.objects.all():
            for month in [1, 2, 3, 4, 5, 6, 7, 8]:
                timestamp = '2018-0{}-01 00:00:00 UTC'.format(month)

                for bnf_code in bnf_codes:
                    items = randint(0, 100)
                    quantity = randint(6, 28) * items
                    actual_cost =  randint(100, 200) * quantity * 0.01

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
        call_command('import_measures', measure='lpzomnibus,measure_1,measure_2')

        # Clean up.
        for ix in range(3):
            if ix == 0:
                measure_id = 'lpzomnibus'
            else:
                measure_id = 'measure_{}'.format(ix)

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
