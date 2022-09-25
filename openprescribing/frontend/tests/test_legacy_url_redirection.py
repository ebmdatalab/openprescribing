from django.test import TestCase
from frontend.models import PCT, STP


class TestLegacyUrlRedirection(TestCase):
    def test_ccg_to_sicbl(self):
        PCT.objects.create(code="000")
        rsp = self.client.get("/ccg/000/")
        self.assertEqual(rsp.url, "/sicbl/000/")

    def test_by_ccg_to_by_sicbl(self):
        PCT.objects.create(code="000")
        rsp = self.client.get("/api/1.0/spending_by_ccg?format=csv&org=000")
        self.assertEqual(rsp.url, "/api/1.0/spending_by_sicbl?format=csv&org=000")

    def test_stp_to_icb(self):
        STP.objects.create(code="000")
        rsp = self.client.get("/stp/000/")
        self.assertEqual(rsp.url, "/icb/000/")

    def test_by_stp_to_by_icb(self):
        PCT.objects.create(code="000")
        rsp = self.client.get("/api/1.0/spending_by_stp?format=csv&org=000")
        self.assertEqual(rsp.url, "/api/1.0/spending_by_icb?format=csv&org=000")

    def test_stp_with_ons_code_to_icb(self):
        STP.objects.create(code="000", ons_code="E00000000")
        rsp = self.client.get("/stp/E00000000/")
        self.assertEqual(rsp.url, "/icb/000/")
