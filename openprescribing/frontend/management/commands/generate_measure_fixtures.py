# This task generates the fixtures in frontend/tests/fixtures/functional-measures-dont-edit.json.
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
#
# When run, the test environment is automatically selected (see manage.py)
# reducing the risk of trampling over production data.  However, the local
# database (whatever the DATABASES setting points to) does get written to, and
# this task expects that databsae to be empty.  Intermediate data is written to
# BigQuery and is available for BQ_DEFAULT_TABLE_EXPIRATION_MS.


import csv
import itertools
import json
import os
import tempfile
from random import randint

from django.conf import settings
from django.core.management import BaseCommand, call_command

from frontend import bq_schemas as schemas
from frontend.models import (
    ImportLog,
    Measure,
    MeasureGlobal,
    MeasureValue,
    Practice,
    Prescription,
    PCN,
    PCT,
    STP,
    RegionalTeam,
)
from gcutils.bigquery import Client
from matrixstore.tests.contextmanagers import (
    patched_global_matrixstore_from_data_factory,
)
from matrixstore.tests.data_factory import DataFactory


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # Ensure that we'll use the test BQ instance
        assert settings.BQ_PROJECT == "ebmdatalabtest", settings.BQ_PROJECT

        # Ensure we won't pick up any unexpected models
        for model in [
            Measure,
            MeasureGlobal,
            MeasureValue,
            Practice,
            Prescription,
            PCT,
            STP,
            RegionalTeam,
        ]:
            assert model.objects.count() == 0, model

        # Delete any ImportLogs that were created by migrations
        ImportLog.objects.all().delete()

        # Create a bunch of RegionalTeams, STPs, CCGs, Practices
        for regtm_ix in range(2):
            regtm = RegionalTeam.objects.create(
                code="Y0{}".format(regtm_ix), name="Region {}".format(regtm_ix)
            )

            for stp_ix in range(2):
                stp = STP.objects.create(
                    ons_code="E000000{}{}".format(regtm_ix, stp_ix),
                    name="STP {}/{}".format(regtm_ix, stp_ix),
                )

                pcns = []
                for pcn_ix in range(2):
                    pcn = PCN.objects.create(
                        code="E00000{}{}{}".format(regtm_ix, stp_ix, pcn_ix),
                        name="PCN {}/{}/{}".format(regtm_ix, stp_ix, pcn_ix),
                    )
                    pcns.append(pcn)
                # Function to return next PCN, looping round forever
                get_next_pcn = itertools.cycle(pcns).__next__

                for ccg_ix in range(2):
                    ccg = PCT.objects.create(
                        regional_team=regtm,
                        stp=stp,
                        code="{}{}{}".format(regtm_ix, stp_ix, ccg_ix).replace(
                            "0", "A"
                        ),
                        name="CCG {}/{}/{}".format(regtm_ix, stp_ix, ccg_ix),
                        org_type="CCG",
                    )

                    for prac_ix in range(2):
                        Practice.objects.create(
                            ccg=ccg,
                            pcn=get_next_pcn(),
                            code="P0{}{}{}{}".format(regtm_ix, stp_ix, ccg_ix, prac_ix),
                            name="Practice {}/{}/{}/{}".format(
                                regtm_ix, stp_ix, ccg_ix, prac_ix
                            ),
                            setting=4,
                            address1="",
                            address2="",
                            address3="",
                            address4="",
                            address5="",
                            postcode="",
                        )

        # import_measures uses this ImportLog to work out which months it
        # should import data.
        ImportLog.objects.create(category="prescribing", current_at="2018-08-01")
        # The practice, CCG etc dashboards use this date
        ImportLog.objects.create(category="dashboard_data", current_at="2018-08-01")

        # Set up BQ, and upload STPs, CCGs, Practices.
        Client("measures").create_dataset()
        client = Client("hscic")
        table = client.get_or_create_table("ccgs", schemas.CCG_SCHEMA)
        table.insert_rows_from_pg(
            PCT, schemas.CCG_SCHEMA, transformer=schemas.ccgs_transform
        )
        table = client.get_or_create_table("practices", schemas.PRACTICE_SCHEMA)
        table.insert_rows_from_pg(Practice, schemas.PRACTICE_SCHEMA)

        # Create measures definitions and record the BNF codes used
        bnf_codes = []

        for ix in range(5):
            numerator_bnf_codes_filter = ["0{}01".format(ix)]
            denominator_bnf_codes_filter = ["0{}".format(ix)]

            if ix in [0, 1]:
                measure_id = "core_{}".format(ix)
                name = "Core measure {}".format(ix)
                tags = ["core"]
                tags_focus = None
            elif ix in [2, 3]:
                measure_id = "lp_{}".format(ix)
                name = "LP measure {}".format(ix)
                tags = ["lowpriority"]
                tags_focus = None
            else:
                assert ix == 4
                measure_id = "lpzomnibus"
                name = "LP omnibus measure"
                tags = ["core"]
                tags_focus = ["lowpriority"]
                numerator_bnf_codes_filter = ["0201", "0301"]
                denominator_bnf_codes_filter = ["02", "03"]

            measure_definition = {
                "name": name,
                "title": "{} Title".format(ix),
                "description": "{} description".format(name),
                "why_it_matters": "Why {} matters".format(name),
                "url": "http://example.com/measure-{}".format(measure_id),
                "numerator_short": "Numerator for {}".format(measure_id),
                "numerator_type": "bnf_quantity",
                "numerator_bnf_codes_filter": numerator_bnf_codes_filter,
                "denominator_short": "Denominator for {}".format(measure_id),
                "denominator_type": "bnf_quantity",
                "denominator_bnf_codes_filter": denominator_bnf_codes_filter,
                "is_cost_based": True,
                "is_percentage": True,
                "low_is_good": True,
                "tags": tags,
                "tags_focus": tags_focus,
            }

            path = os.path.join(
                settings.MEASURE_DEFINITIONS_PATH, "{}.json".format(measure_id)
            )
            with open(path, "w") as f:
                json.dump(measure_definition, f, indent=2)

            bnf_codes.append("0{}0000000000000".format(ix))
            bnf_codes.append("0{}0100000000000".format(ix))

        # Generate random prescribing data. We don't currently save this to the
        # database as it would make the fixture too big and isn't needed.
        # Later we create the minimal prescribing needed by the MatrixStore.
        prescribing_rows = []

        timestamps = [
            "2018-0{}-01 00:00:00 UTC".format(month)
            for month in [1, 2, 3, 4, 5, 6, 7, 8]
        ]

        for practice_ix, practice in enumerate(Practice.objects.all()):
            for month, timestamp in enumerate(timestamps, start=1):

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
                        "sha",  # This value doesn't matter.
                        practice.ccg_id,
                        practice.code,
                        bnf_code,
                        "bnf_name",  # This value doesn't matter
                        items,
                        net_cost,
                        actual_cost,
                        quantity,
                        timestamp,
                    ]

                    prescribing_rows.append(row)

        # Create the minimal amount of prescribing necessary for the
        # MatrixStore to build and for the PPU calculation to work
        # successfully. This means at least one prescription for a branded
        # presentation and its generic equivalent.
        for bnf_code in ["0601022B0AAASAS", "0601022B0BJADAS"]:
            bnf_codes.append(bnf_code)

            practice = Practice.objects.all()[0]
            timestamp = timestamps[-1]
            # It doesn't really matter what these values are but it's nice for
            # them to be both predictable and different
            items = len(bnf_codes)
            quantity = 50 * len(bnf_codes)
            net_cost = 10 * len(bnf_codes) + 1000
            actual_cost = net_cost * 0.93

            row = [
                "sha",  # This value doesn't matter.
                practice.ccg_id,
                practice.code,
                bnf_code,
                "bnf_name",  # This value doesn't matter
                items,
                net_cost,
                actual_cost,
                quantity,
                timestamp,
            ]
            prescribing_rows.append(row)

            # Unlike the measure prescribing we created earlier this
            # prescribing needs to be written to the database so it gets
            # included in the fixture we create
            Prescription.objects.create(
                practice_id=row[2],
                pct_id=row[1],
                presentation_code=row[3],
                total_items=row[5],
                net_cost=row[6],
                actual_cost=row[7],
                quantity=row[8],
                processing_date=row[9][:10],
            )

        # Upload presentations to BigQuery: the new measures system requires them
        table = client.get_or_create_table("presentation", schemas.PRESENTATION_SCHEMA)
        with tempfile.NamedTemporaryFile(mode="wt", encoding="utf8", newline="") as f:
            writer = csv.DictWriter(
                f, [field.name for field in schemas.PRESENTATION_SCHEMA]
            )
            for bnf_code in bnf_codes:
                writer.writerow({"bnf_code": bnf_code})
            f.seek(0)
            table.insert_rows_from_csv(f.name, schemas.PRESENTATION_SCHEMA)

        # In production, normalised_prescribing is actually a view,
        # but for the tests it's much easier to set it up as a normal table.
        table = client.get_or_create_table(
            "normalised_prescribing", schemas.PRESCRIBING_SCHEMA
        )

        # Upload prescribing_rows to normalised_prescribing.
        with tempfile.NamedTemporaryFile(mode="wt", encoding="utf8", newline="") as f:
            writer = csv.writer(f)
            for row in prescribing_rows:
                writer.writerow(row)
            f.seek(0)
            table.insert_rows_from_csv(f.name, schemas.PRESCRIBING_SCHEMA)

        # Create some dummy prescribing data in the MatrixStore.
        factory = DataFactory()
        month = factory.create_months("2018-10-01", 1)[0]
        practice = factory.create_practices(1)[0]
        for bnf_code in bnf_codes:
            presentation = factory.create_presentation(bnf_code)
            factory.create_prescription(presentation, practice, month)

        # Do the work.
        with patched_global_matrixstore_from_data_factory(factory):
            call_command(
                "import_measures", measure="core_0,core_1,lp_2,lp_3,lpzomnibus"
            )

        # Clean up.
        for ix in range(5):
            if ix in [0, 1]:
                measure_id = "core_{}".format(ix)
            elif ix in [2, 3]:
                measure_id = "lp_{}".format(ix)
            else:
                assert ix == 4
                measure_id = "lpzomnibus"

            path = os.path.join(
                settings.MEASURE_DEFINITIONS_PATH, "{}.json".format(measure_id)
            )
            os.remove(path)

        # Dump the fixtures.
        fixture_path = os.path.join(
            "frontend", "tests", "fixtures", "functional-measures-dont-edit.json"
        )
        call_command("dumpdata", "frontend", indent=2, output=fixture_path)
