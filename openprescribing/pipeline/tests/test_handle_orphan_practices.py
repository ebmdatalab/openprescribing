import mock
import os
from StringIO import StringIO
import sys

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from frontend.models import PCT


class CommandTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # See gen_epraccurs.py for details of test data
        for code, name in [
            ['C01', 'NHS LOSES SOME PRACTICES TO C02'],
            ['C02', 'NHS GAINS SOME PRACTICES FROM C01'],
            ['C03', 'NHS GAINS SOME PRACTICES FROM C04'],
            ['C04', 'NHS CLOSES LOSING PRACTICES TO C03 AND C06'],
            ['C05', 'NHS CLOSES LOSING PRACTICES TO C06'],
            ['C06', 'NHS OPENS GAINING PRACTICES FROM C04 AND C05'],
        ]:
            PCT.objects.create(code=code, name=name, org_type='CCG')

        path = os.path.join(settings.SITE_ROOT, 'pipeline', 'test-data')
        cls.path1 = os.path.join(path, 'epraccur1.csv')
        cls.path2 = os.path.join(path, 'epraccur2.csv')

        call_command('import_practices', '--epraccur', cls.path1)
        call_command('import_practices', '--epraccur', cls.path2)

    @mock.patch('pipeline.management.commands.handle_orphan_practices.notify_slack')
    def test_wet_run(self, notify_slack):
        ccg_id_to_closed_practices = {
            ccg.code: list(ccg.practice_set.exclude(status_code='A'))
            for ccg in PCT.objects.all()
        }

        call_command(
            'handle_orphan_practices',
            '--prev-path', self.path1,
            '--curr-path', self.path2
        )

        # We expect closed practices in C01 and C04 not to have moved
        for practice in ccg_id_to_closed_practices['C01']:
            practice.refresh_from_db()
            self.assertEqual(practice.ccg_id, 'C01')

        for practice in ccg_id_to_closed_practices['C04']:
            practice.refresh_from_db()
            self.assertEqual(practice.ccg_id, 'C04')

        # We expect closed practices in C05 to have moved to C06
        for practice in ccg_id_to_closed_practices['C05']:
            practice.refresh_from_db()
            self.assertEqual(practice.ccg_id, 'C06')

        self.assertEqual(notify_slack.call_count, 2)
        msgs = [c[0][0] for c in notify_slack.call_args_list]
        self.assertIn('Practices have left CCG C01', msgs[0])
        self.assertIn('Active practices previously in CCG C04', msgs[1])

    @mock.patch('pipeline.management.commands.handle_orphan_practices.notify_slack')
    def test_dry_run(self, notify_slack):
        # This is just exercising the code
        try:
            orig_stdout = sys.stdout
            new_stdout = StringIO()
            sys.stdout = new_stdout

            call_command(
                'handle_orphan_practices',
                '--dry-run',
                '--prev-path', self.path1,
                '--curr-path', self.path2
            )

            self.assertFalse(notify_slack.called)

        finally:
            sys.stdout = orig_stdout
