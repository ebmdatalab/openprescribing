from django.core import mail
from django.core.management import call_command
from frontend.models import ImportLog, MeasureGlobal
from frontend.tests.data_factory import DataFactory
from frontend.tests.test_api_spending import ApiTestBase


class CommandTestCase(ApiTestBase):
    fixtures = ApiTestBase.fixtures + ["functional-measures-dont-edit"]

    @classmethod
    def setUpTestData(cls):
        super(CommandTestCase, cls).setUpTestData()
        max_measure_date = MeasureGlobal.objects.order_by("-month")[0].month
        ImportLog.objects.create(current_at=max_measure_date, category="dashboard_data")

    def test_send_alerts(self):
        factory = DataFactory()

        # Create a bookmark, send alerts, and make sure one email is sent to
        # correct user
        bookmark = factory.create_org_bookmark(None)
        call_command("send_all_england_alerts")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [bookmark.user.email])

        # Create another bookmark, send alerts again and make sure email is
        # only sent to new user
        mail.outbox = []
        bookmark2 = factory.create_org_bookmark(None)
        call_command("send_all_england_alerts")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [bookmark2.user.email])

        # Try sending alerts again and make sure no emails are sent
        mail.outbox = []
        call_command("send_all_england_alerts")
        self.assertEqual(len(mail.outbox), 0)
