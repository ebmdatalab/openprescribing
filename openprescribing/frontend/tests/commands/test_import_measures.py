from numbers import Number
import argparse
import json
import os

from gcutils.bigquery import Client
from mock import patch

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from frontend.bq_schemas import CCG_SCHEMA, PRACTICE_SCHEMA, PRESCRIBING_SCHEMA
from frontend.management.commands.import_measures import Command
from frontend.management.commands.import_measures import parse_measures
from frontend.models import ImportLog
from frontend.models import Measure
from frontend.models import MeasureValue, MeasureGlobal, Chemical
from frontend.models import PCT
from frontend.models import Practice
from frontend.models import STP
from frontend.models import RegionalTeam


MODULE = "frontend.management.commands.import_measures"


class UnitTests(TestCase):
    """Unit tests with mocked bigquery. Many of the functional
    tests could be moved hree.

    """

    fixtures = ["measures"]

    @patch("common.utils.db")
    def test_reconstructor_not_called_when_measures_specified(self, db):
        from frontend.management.commands.import_measures import (
            conditional_constraint_and_index_reconstructor,
        )

        with conditional_constraint_and_index_reconstructor({"measure": "thingy"}):
            pass
        execute = db.connection.cursor.return_value.__enter__.return_value.execute
        execute.assert_not_called()

    @patch("common.utils.db")
    def test_reconstructor_called_when_no_measures_specified(self, db):
        from frontend.management.commands.import_measures import (
            conditional_constraint_and_index_reconstructor,
        )

        with conditional_constraint_and_index_reconstructor({"measure": None}):
            pass
        execute = db.connection.cursor.return_value.__enter__.return_value.execute
        execute.assert_called()


class TestParseMeasures(TestCase):
    def test_parse_measures(self):
        measure_defs_path = os.path.join(settings.APPS_ROOT, "measure_definitions")
        with override_settings(MEASURE_DEFINITIONS_PATH=measure_defs_path):
            measures = parse_measures()
        lpzomnibus_ix = list(measures).index("lpzomnibus")
        lptrimipramine_ix = list(measures).index("lptrimipramine")
        # The order of these specific measures matters, as the SQL for
        # the omnibus measure relies on the other LP measures having
        # been calculated first
        self.assertTrue(lptrimipramine_ix < lpzomnibus_ix)
