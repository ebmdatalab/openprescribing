import csv

from django.http import Http404
from django.test import TestCase

from frontend.models import Prescription, ImportLog

from matrixstore.tests.matrixstore_factory import (
    matrixstore_from_postgres,
    patch_global_matrixstore,
)


class ApiTestBase(TestCase):
    """Base test case that sets up all the fixtures required by any of the
    API tests.

    """

    fixtures = [
        "orgs",
        "practices",
        "practice_listsizes",
        "products",
        "presentations",
        "sections",
        "prescriptions",
        "chemicals",
    ]
    api_prefix = "/api/1.0"

    @classmethod
    def setUpTestData(cls):
        # Create an ImportLog entry for the latest prescribing date we have
        date = Prescription.objects.latest("processing_date").processing_date
        ImportLog.objects.create(current_at=date, category="prescribing")
        matrixstore = matrixstore_from_postgres()
        stop_patching = patch_global_matrixstore(matrixstore)
        # Have to wrap this in a staticmethod decorator otherwise Python thinks
        # we're trying to create a new class method
        cls._stop_patching = staticmethod(stop_patching)

    @classmethod
    def tearDownClass(cls):
        cls._stop_patching()
        super(ApiTestBase, cls).tearDownClass()

    def _rows_from_api(self, url):
        url = self.api_prefix + url
        response = self.client.get(url, follow=True)
        if response.status_code == 404:
            raise Http404("URL %s does not exist" % url)
        reader = csv.DictReader(response.content.splitlines())
        rows = []
        for row in reader:
            rows.append(row)
        return rows
