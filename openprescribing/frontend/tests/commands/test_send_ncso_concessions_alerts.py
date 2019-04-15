from mock import patch

from django.core import mail
from django.core.management import call_command
from django.test import TestCase

from frontend.tests.data_factory import DataFactory


@patch('frontend.views.bookmark_utils.attach_image')
class CommandTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        factory = DataFactory()
        cls.months = factory.create_months_array(
            start_date='2018-02-01', num_months=6)
        # Our NCSO and tariff data extends further than our prescribing data by
        # a couple of months
        cls.prescribing_months = cls.months[:-2]
        # Create some CCGs (we need more than one so we can test aggregation
        # across CCGs at the All England level)
        cls.ccgs = [factory.create_ccg() for _ in range(2)]
        # Populate those CCGs with practices
        cls.practices = []
        for ccg in cls.ccgs:
            for _ in range(2):
                cls.practices.append(factory.create_practice(ccg=ccg))
        # Create some presentations
        cls.presentations = factory.create_presentations(6)
        # Create drug tariff and price concessions costs for these presentations
        factory.create_tariff_and_ncso_costings_for_presentations(
            cls.presentations,
            months=cls.months)
        # Create prescribing for each of the practices we've created
        for practice in cls.practices:
            factory.create_prescribing_for_practice(
                practice,
                presentations=cls.presentations,
                months=cls.prescribing_months
            )
        # Create and populate the materialized view table we need
        factory.populate_materialised_views()
        # Pull out an individual practice and CCG to use in our tests
        cls.practice = cls.practices[0]
        cls.ccg = cls.ccgs[0]

    def test_send_alerts(self, attach_image):
        factory = DataFactory()

        # Create a bookmark, send alerts, and make sure one email is sent.
        factory.create_ncso_concessions_bookmark(self.ccg)
        call_command('send_ncso_concessions_alerts', '2019-02-14')
        self.assertEqual(len(mail.outbox), 1)

        # Create another bookmark, send alerts for same date as above, and make
        # sure only one email is sent.
        mail.outbox = []
        factory.create_ncso_concessions_bookmark(self.practice)
        call_command('send_ncso_concessions_alerts', '2019-02-14')
        self.assertEqual(len(mail.outbox), 1)

        # Send alerts for new date, and make sure two emails are sent.
        mail.outbox = []
        call_command('send_ncso_concessions_alerts', '2019-02-15')
        self.assertEqual(len(mail.outbox), 2)
