from django.test import TestCase
from frontend.models import PCT
from matrixstore.tests.data_factory import DataFactory
from matrixstore.tests.matrixstore_factory import (
    matrixstore_from_data_factory,
    patch_global_matrixstore,
)
from outliers.build import prescribing_for_orgs


class BuildTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        factory = DataFactory()
        factory.create_all(
            start_date="2018-06-01", num_months=6, num_practices=6, num_presentations=6
        )
        ccg = PCT.objects.create(code="ABC", org_type="CCG")
        for i in range(6):
            ccg.practice_set.create(code=f"ABC00{i}", setting=4)

        cls._remove_patch = patch_global_matrixstore(
            matrixstore_from_data_factory(factory)
        )

    def test_build_smoke_test(self):
        # The data produced by the DataFactory is not rich enough to test anything
        # interesting, but this is a reasonable smoke test that the calculations work.
        df = prescribing_for_orgs("2018-06-01", "2018-09-01", "practice")
        assert len(df) == 6

    @classmethod
    def tearDownClass(cls):
        cls._remove_patch()
        super().tearDownClass()
