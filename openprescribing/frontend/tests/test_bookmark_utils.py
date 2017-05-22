from dateutil.relativedelta import relativedelta
import os
import unittest

from django.test import TestCase
import base64
from datetime import datetime
from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer
import socket
from threading import Thread
import requests
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from mock import patch
from mock import MagicMock

from frontend.models import ImportLog
from frontend.models import Measure
from frontend.models import MeasureValue
from frontend.models import PCT
from frontend.models import Practice
from frontend.views import bookmark_utils


class IntroTextTest(unittest.TestCase):
    def test_nothing(self):
        stats = _makeContext(possible_top_savings_total=9000.1)
        msg = bookmark_utils.getIntroText(stats, 'CCG')
        self.assertIn("We've no new information about this CCG", msg)

    def test_worst(self):
        stats = _makeContext(worst=[None])
        msg = bookmark_utils.getIntroText(stats, 'CCG')
        self.assertNotIn("We've no new information about this CCG", msg)
        self.assertIn("We've found one prescribing measure where this "
                      "CCG could be <span class='worse'>doing better", msg)

    def test_worst_plural(self):
        stats = _makeContext(worst=[None, None])
        msg = bookmark_utils.getIntroText(stats, 'CCG')
        self.assertIn("We've found two prescribing measures where this "
                      "CCG could be <span class='worse'>doing better", msg)

    def test_decline_plural(self):
        stats = _makeContext(declines=[None, None])
        msg = bookmark_utils.getIntroText(stats, 'CCG')
        self.assertIn("We've found two prescribing measures where this "
                      "CCG is <span class='worse'>getting worse", msg)

    def test_decline_and_worse(self):
        stats = _makeContext(declines=[None], worst=[None])
        msg = bookmark_utils.getIntroText(stats, 'thing')
        self.assertIn("We've found two prescribing measures where this "
                      "thing is <span class='worse'>getting worse, "
                      "or could be doing better", msg)

    def test_improvement(self):
        stats = _makeContext(improvements=[None])
        msg = bookmark_utils.getIntroText(stats, 'thing')
        self.assertIn("We've found one prescribing measure where this "
                      "thing is <span class='better'>improving", msg)

    def test_improvement_and_best(self):
        stats = _makeContext(improvements=[None], best=[None])
        msg = bookmark_utils.getIntroText(stats, 'thing')
        self.assertIn("We've found two prescribing measures where this "
                      "thing is <span class='better'>doing well", msg)

    def test_decline_and_improvement(self):
        stats = _makeContext(declines=[None], improvements=[None])
        msg = bookmark_utils.getIntroText(stats, 'thing')
        self.assertIn("We've found one prescribing measure where this "
                      "thing is <span class='worse'>getting worse</span>, "
                      "and one measure where it is <span class='better'>"
                      "improving", msg)

    def test_possible_savings(self):
        stats = _makeContext(possible_savings=[None])
        msg = bookmark_utils.getIntroText(stats, 'thing')
        self.assertIn("We've also found one prescribing measure where there "
                      "are some potential cost savings", msg)


class TestCUSUM(unittest.TestCase):
    def extract_percentiles_for_alerts(self, result):
        neg = result['alert_percentile_neg']
        pos = result['alert_percentile_pos']
        print pos
        combined = []
        assert len(neg) == len(pos)
        for i, val in enumerate(neg):
            if val:
                assert not pos[i]
                combined.append('d')
            elif pos[i]:
                combined.append('u')
            else:
                combined.append(' ')
        return "   ".join(combined).rstrip()

    def test_percentiles_at_extremes_one_extreme_ok(self):
        with open(
                settings.SITE_ROOT + '/frontend/tests/fixtures/'
                'alert_test_cases.txt', 'rb') as expected:
            test_cases = expected.readlines()
        import re
        import json
        alignment_header = '*'.join(['...'] * 12)
        for i in range(0, len(test_cases), 4):
            assert test_cases[i].startswith("#"), "At line %s: %s does not start with #" % (i, test_cases[i])
            test_name = test_cases[i].strip()
            if not test_name.startswith("# Linear increase with "):
                continue
            assert test_cases[i+1][3::4].strip() == '', "%s: Every column must be three wide followed by a space: \n%s\n%s" % (test_name, alignment_header, test_cases[i+1])
            directions = [n for n, ltr in enumerate(test_cases[i+2]) if ltr in ('u', 'd')]
            assert sum([x % 4 for x in directions]) == 0, "%s: Every column must be three wide followed by a space:\n%s\n%s" % (test_name, alignment_header,  str(test_cases[i+2]))
            data = [round(int(x)/100.0,2) if x.strip() else None for x in re.findall('(   |\d+ {0,2}) ?', test_cases[i+1])]
            old_result = bookmark_utils.cusum(data, 3, 5)
            new_result = bookmark_utils.CUSUM(data, window_size=3, sensitivity=5).work()
            old_result_formatted = self.extract_percentiles_for_alerts(old_result)
            new_result_formatted = self.extract_percentiles_for_alerts(new_result)
            expected = test_cases[i+2].rstrip()
            error_message = "In test '%s':\n" % test_name
            error_message += "   Input values: %s" % test_cases[i+1]
            error_message += "Expected alerts: %s" % test_cases[i+2]
            print test_name
            print "-" * 78
            print json.dumps(new_result, indent=2)
            print json.dumps(old_result, indent=2)  # the old version appends an extra alert_percentile_pos which I think is actually right
            self.assertEqual(
                old_result_formatted,
                expected,
                error_message + "            Got: %s" % old_result_formatted)
            self.assertEqual(
                new_result_formatted,
                expected,
                error_message + "            Got: %s" % new_result_formatted)
            #self.assertEqual(old_result['alert'], new_result['alert'])
            #print test_name
            #print "-" * 78
            #print json.dumps(old_result, indent=2)
            #print json.dumps(new_result, indent=2)
            #print self.assertEqual(json.dumps(old_result, indent=2), json.dumps(new_result, indent=2))

class TestBookmarkUtilsPerforming(TestCase):
    fixtures = ['bookmark_alerts', 'measures']

    def setUp(self):
        self.measure_id = 'cerazette'
        self.measure = Measure.objects.get(pk=self.measure_id)
        self.measure.low_is_good = True
        self.measure.save()
        pct = PCT.objects.get(pk='03V')
        practice_with_high_percentiles = Practice.objects.get(pk='P87629')
        practice_with_low_percentiles = Practice.objects.get(pk='P87630')
        ImportLog.objects.create(
            category='prescribing',
            current_at=datetime.today())
        for i in range(3):
            month = datetime.today() + relativedelta(months=i)
            MeasureValue.objects.create(
                measure=self.measure,
                practice=None,
                pct=pct,
                percentile=95,
                month=month
            )
            MeasureValue.objects.create(
                measure=self.measure,
                practice=practice_with_high_percentiles,
                pct=pct,
                percentile=95,
                month=month
            )
            MeasureValue.objects.create(
                measure=self.measure,
                practice=practice_with_low_percentiles,
                pct=pct,
                percentile=5,
                month=month
            )
        self.pct = pct
        self.high_percentile_practice = practice_with_high_percentiles
        self.low_percentile_practice = practice_with_low_percentiles

    # Worst performing
    # CCG bookmarks
    def test_hit_where_ccg_worst_in_specified_number_of_months(self):
        finder = bookmark_utils.InterestingMeasureFinder(
            pct=self.pct)
        worst_measures = finder.worst_performing_in_period(3)
        self.assertIn(self.measure, worst_measures)

    def test_miss_where_not_better_in_specified_number_of_months(self):
        self.measure.low_is_good = False
        self.measure.save()
        finder = bookmark_utils.InterestingMeasureFinder(
            pct=self.pct)
        worst_measures = finder.worst_performing_in_period(3)
        self.assertFalse(worst_measures)

    def test_miss_where_not_enough_global_data(self):
        finder = bookmark_utils.InterestingMeasureFinder(
            pct=self.pct)
        worst_measures = finder.worst_performing_in_period(6)
        self.assertFalse(worst_measures)

    def test_miss_where_not_worst_in_specified_number_of_months(self):
        MeasureValue.objects.all().delete()
        finder = bookmark_utils.InterestingMeasureFinder(
            pct=self.pct)
        worst_measures = finder.worst_performing_in_period(3)
        self.assertFalse(worst_measures)

    # Practice bookmarks
    def test_hit_where_practice_worst_in_specified_number_of_months(self):
        finder = bookmark_utils.InterestingMeasureFinder(
            practice=self.high_percentile_practice)
        worst_measures = finder.worst_performing_in_period(3)
        self.assertIn(self.measure, worst_measures)

    # Best performing
    def test_hit_where_practice_best_in_specified_number_of_months(self):
        finder = bookmark_utils.InterestingMeasureFinder(
            practice=self.low_percentile_practice)
        best_measures = finder.best_performing_in_period(3)
        self.assertIn(self.measure, best_measures)

    def test_no_hit_where_practice_best_and_low_is_bad(self):
        self.measure.low_is_good = False
        self.measure.save()
        finder = bookmark_utils.InterestingMeasureFinder(
            practice=self.low_percentile_practice)
        best_measures = finder.best_performing_in_period(3)
        self.assertFalse(best_measures)


class TestBookmarkUtilsChanging(TestCase):
    fixtures = ['bookmark_alerts', 'measures']

    def setUp(self):
        self.measure_id = 'cerazette'
        self.measure = Measure.objects.get(pk=self.measure_id)
        ImportLog.objects.create(
            category='prescribing',
            current_at=datetime.today())
        practice_with_high_change = Practice.objects.get(pk='P87629')
        practice_with_high_neg_change = Practice.objects.get(pk='P87631')
        practice_with_low_change = Practice.objects.get(pk='P87630')
        for i in range(3):
            month = datetime.today() + relativedelta(months=i)
            MeasureValue.objects.create(
                measure=self.measure,
                practice=practice_with_high_change,
                percentile=(i+1) * 7,
                month=month
            )
            MeasureValue.objects.create(
                measure=self.measure,
                practice=practice_with_high_neg_change,
                percentile=(3-i) * 7,
                month=month
            )
            MeasureValue.objects.create(
                measure=self.measure,
                practice=practice_with_low_change,
                percentile=i+1,
                month=month
            )
        self.practice_with_low_change = practice_with_low_change
        self.practice_with_high_change = practice_with_high_change
        self.practice_with_high_neg_change = practice_with_high_neg_change

    def test_low_change_not_returned_for_practice(self):
        finder = bookmark_utils.InterestingMeasureFinder(
            practice=self.practice_with_low_change,
            interesting_percentile_change=10
        )
        self.assertEqual(finder.most_change_in_period(3),
                         {'improvements': [],
                          'declines': []})

    def test_low_change_not_returned_for_ccg(self):
        # This test will raise a warning due to all imput being
        # None. Silence it.
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            finder = bookmark_utils.InterestingMeasureFinder(
                pct=self.practice_with_low_change.ccg,
                interesting_percentile_change=10
            )
            self.assertEqual(finder.most_change_in_period(3),
                             {'improvements': [],
                              'declines': []})

    def test_high_change_returned(self):
        finder = bookmark_utils.InterestingMeasureFinder(
            practice=self.practice_with_high_change,
            interesting_percentile_change=10)
        sorted_measure = finder.most_change_in_period(3)
        measure_info = sorted_measure['improvements'][0]
        self.assertEqual(
            measure_info[0].id, 'cerazette')
        self.assertAlmostEqual(
            measure_info[1], 7)   # start
        self.assertAlmostEqual(
            measure_info[2], 21)  # end
        self.assertAlmostEqual(
            measure_info[3], 0)   # residuals

    def test_high_change_declines_when_low_is_good(self):
        self.measure.low_is_good = True
        self.measure.save()
        finder = bookmark_utils.InterestingMeasureFinder(
            practice=self.practice_with_high_change,
            interesting_percentile_change=10)
        sorted_measure = finder.most_change_in_period(3)
        measure_info = sorted_measure['declines'][0]
        self.assertEqual(
            measure_info[0].id, 'cerazette')
        self.assertAlmostEqual(
            measure_info[1], 7)   # start
        self.assertAlmostEqual(
            measure_info[2], 21)  # end
        self.assertAlmostEqual(
            measure_info[3], 0)   # residuals

    def test_high_negative_change_returned(self):
        finder = bookmark_utils.InterestingMeasureFinder(
            practice=self.practice_with_high_neg_change,
            interesting_percentile_change=10)
        sorted_measure = finder.most_change_in_period(3)
        measure_info = sorted_measure['declines'][0]
        self.assertEqual(
            measure_info[0].id, 'cerazette')
        self.assertAlmostEqual(
            measure_info[1], 21)  # start
        self.assertAlmostEqual(
            measure_info[2], 7)   # end
        self.assertAlmostEqual(
            measure_info[3], 0)   # residuals


def _makeCostSavingMeasureValues(measure, practice, savings):
    """Create measurevalues for the given practice and measure with
    savings at the 50th centile taken from the specified `savings`
    array.  Savings at the 90th centile are set as 100 times those at
    the 50th, and at the 10th as 0.1 times.

    """
    for i in range(len(savings)):
        month = datetime.today() + relativedelta(months=i)
        MeasureValue.objects.create(
            measure=measure,
            practice=practice,
            percentile=0.5,
            cost_savings={
                '10': savings[i] * 0.1,
                '50': savings[i],
                '90': savings[i] * 100, },
            month=month
        )


class TestBookmarkUtilsSavingsBase(TestCase):
    fixtures = ['bookmark_alerts', 'measures']

    def setUp(self):
        self.measure_id = 'cerazette'
        self.measure = Measure.objects.get(pk=self.measure_id)
        ImportLog.objects.create(
            category='prescribing',
            current_at=datetime.today())
        self.practice = Practice.objects.get(pk='P87629')


class TestBookmarkUtilsSavingsPossible(TestBookmarkUtilsSavingsBase):
    def setUp(self):
        super(TestBookmarkUtilsSavingsPossible, self).setUp()
        _makeCostSavingMeasureValues(
            self.measure, self.practice, [0, 1500, 2000])

    def test_possible_savings_for_practice(self):
        finder = bookmark_utils.InterestingMeasureFinder(
            practice=self.practice)
        savings = finder.top_and_total_savings_in_period(3)
        self.assertEqual(savings['possible_savings'], [(self.measure, 3500)])
        self.assertEqual(savings['achieved_savings'], [])
        self.assertEqual(savings['possible_top_savings_total'], 350000)

    def test_possible_savings_for_practice_not_enough_months(self):
        finder = bookmark_utils.InterestingMeasureFinder(
            practice=self.practice)
        savings = finder.top_and_total_savings_in_period(10)
        self.assertEqual(savings['possible_savings'], [])
        self.assertEqual(savings['achieved_savings'], [])
        self.assertEqual(savings['possible_top_savings_total'], 0)

    def test_possible_savings_for_ccg(self):
        finder = bookmark_utils.InterestingMeasureFinder(
            pct=self.practice.ccg)
        savings = finder.top_and_total_savings_in_period(3)
        self.assertEqual(savings['possible_savings'], [])
        self.assertEqual(savings['achieved_savings'], [])
        self.assertEqual(savings['possible_top_savings_total'], 0)

    def test_possible_savings_low_is_good(self):
        self.measure.low_is_good = True
        self.measure.save()
        finder = bookmark_utils.InterestingMeasureFinder(
            practice=self.practice)
        savings = finder.top_and_total_savings_in_period(3)
        self.assertEqual(savings['possible_savings'], [(self.measure, 3500)])
        self.assertEqual(savings['achieved_savings'], [])
        self.assertEqual(savings['possible_top_savings_total'], 350.0)


class TestBookmarkUtilsSavingsAchieved(TestBookmarkUtilsSavingsBase):
    def setUp(self):
        super(TestBookmarkUtilsSavingsAchieved, self).setUp()
        _makeCostSavingMeasureValues(
            self.measure, self.practice, [-1000, -500, 100])

    def test_achieved_savings(self):
        finder = bookmark_utils.InterestingMeasureFinder(
            practice=self.practice)
        savings = finder.top_and_total_savings_in_period(3)
        self.assertEqual(savings['possible_savings'], [])
        self.assertEqual(savings['achieved_savings'], [(self.measure, 1400)])
        self.assertEqual(savings['possible_top_savings_total'], 10000)


class MockServerRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == '/page.html':
            self.send_response(requests.codes.ok)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            response_content = """
            <html>
             <head>
              <script src='/jquery.min.js'></script>
              <style>
               div {width: 100%; height: 100%}
               #thing1 {background-color:red}
               #thing1 {background-color:green}
              </style>
             </head>
             <div id='thing1'></div>
             <div id='thing2'></div>
            </html>
            """
            self.wfile.write(response_content)
            return
        elif self.path == '/jquery.min.js':
            self.send_response(requests.codes.ok)
            self.send_header('Content-Type', 'text/javascript')
            self.end_headers()
            with open(settings.SITE_ROOT + '/media/js/'
                      'node_modules/jquery/dist/jquery.min.js', 'r') as f:
                self.wfile.write(f.read())
                return


def get_free_port():
    s = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    address, port = s.getsockname()
    s.close()
    return port


def start_mock_server(port):
    mock_server = HTTPServer(('localhost', port), MockServerRequestHandler)
    mock_server_thread = Thread(target=mock_server.serve_forever)
    mock_server_thread.setDaemon(True)
    mock_server_thread.start()


class GenerateImageTestCase(unittest.TestCase):
    def setUp(self):
        port = get_free_port()
        start_mock_server(port)
        self.msg = EmailMultiAlternatives(
            "Subject", "body", "sender@email.com", ["recipient@email.com"])
        self.url = ":%s/page.html" % port
        self.file_path = "/tmp/image.png"
        self.selector = "#thing2"

    def tearDown(self):
        try:
            os.remove(self.file_path)
        except OSError as e:
            import errno
            # We don't care about a "No such file or directory" error
            if e.errno != errno.ENOENT:
                raise

    def test_image_generated(self):
        self.assertEqual(len(self.msg.attachments), 0)
        image = bookmark_utils.attach_image(
            self.msg, self.url, self.file_path, self.selector)
        with open(
                settings.SITE_ROOT + '/frontend/tests/fixtures/'
                'alert-email-image.png', 'rb') as expected:
            self.assertEqual(len(self.msg.attachments), 1)
            attachment = self.msg.attachments[0]
            # Check the attachment is as we expect
            self.assertEqual(attachment.get_filename(), 'image.png')
            self.assertIn(image, attachment['Content-ID'])
            # Attachments in emails are base64 *with line breaks*, so
            # we remove those.
            self.assertEqual(
                attachment.get_payload().replace("\n", ""),
                base64.b64encode(expected.read()))

    def test_small_image_generated_with_viewport_dimensions_specified(self):
        bookmark_utils.attach_image(
            self.msg, self.url, self.file_path, self.selector, '100x100')
        with open(
                settings.SITE_ROOT + '/frontend/tests/fixtures/'
                'alert-email-image-small.png', 'rb') as expected:
            attachment = self.msg.attachments[0]
            self.assertEqual(
                attachment.get_payload().replace("\n", ""),
                base64.b64encode(expected.read()))


class UnescapeTestCase(unittest.TestCase):
    def test_no_url(self):
        example = "Foo bar"
        self.assertEqual(
            bookmark_utils.unescape_href(example), example)

    def test_unescaped_url(self):
        example = "Foo bar href='http://foo.com/frob?b=3#bar'"
        self.assertEqual(
            bookmark_utils.unescape_href(example), example)

    def test_escaped_url(self):
        example = "href='http://localhost/analyse/?u=7&amp;m=9#bong'"
        expected = "href='http://localhost/analyse/?u=7&m=9#bong'"
        self.assertEqual(
            bookmark_utils.unescape_href(example), expected)

    def test_mixture(self):
        example = ('Foo href="http://localhost/analyse/?u=7&amp;m=9" '
                   'href="http://foo.com/frob?b=3#bar" '
                   'Baz')
        expected = ('Foo href="http://localhost/analyse/?u=7&m=9" '
                    'href="http://foo.com/frob?b=3#bar" '
                    'Baz')
        self.assertEqual(
            bookmark_utils.unescape_href(example), expected)


class TestContextForOrgEmail(unittest.TestCase):
    @patch('frontend.views.bookmark_utils.InterestingMeasureFinder.'
           'worst_performing_in_period')
    @patch('frontend.views.bookmark_utils.InterestingMeasureFinder.'
           'best_performing_in_period')
    @patch('frontend.views.bookmark_utils.InterestingMeasureFinder.'
           'most_change_in_period')
    def test_non_ordinal_sorting(
            self,
            most_change_in_period,
            best_performing_in_period,
            worst_performing_in_period):
        ordinal_measure_1 = MagicMock(low_is_good=True)
        non_ordinal_measure_1 = MagicMock(low_is_good=None)
        non_ordinal_measure_2 = MagicMock(low_is_good=None)
        most_change_in_period.return_value = {
            'improvements': [
                (ordinal_measure_1,)],
            'declines': [(non_ordinal_measure_1,), (non_ordinal_measure_2,)]
        }
        best_performing_in_period.return_value = [
            ordinal_measure_1, non_ordinal_measure_1]
        worst_performing_in_period.return_value = [
            ordinal_measure_1, non_ordinal_measure_1]
        finder = bookmark_utils.InterestingMeasureFinder(
            pct='foo')
        context = finder.context_for_org_email()
        self.assertEqual(
            context['most_changing_interesting'],
            [(non_ordinal_measure_1,), (non_ordinal_measure_2,)])
        self.assertEqual(
            context['interesting'], [non_ordinal_measure_1])
        self.assertEqual(
            context['best'], [ordinal_measure_1])
        self.assertEqual(
            context['worst'], [ordinal_measure_1])
        self.assertEqual(
            context['most_changing']['improvements'], [(ordinal_measure_1,)])


class TruncateSubjectTestCase(unittest.TestCase):
    def test_truncate_subject(self):
        data = [
            {'input': 'short title by me',
             'expected': 'Your monthly update about Short Title by Me'},
            {'input': 'THING IN CAPS',
             'expected': 'Your monthly update about Thing in Caps'},
            {'input':
             ('Items for Abacavir + Levocabastine + Levacetylmethadol '
              'Hydrochloride + 5-Hydroxytryptophan vs Frovatriptan + '
              'Alverine Citrate + Boceprevir by All CCGs'),
             'expected':
             ('Your monthly update about Items for Abacavir + Levocaba...'
              'by All CCGs')},
            {'input':
             ('The point is that the relative freedom which we enjoy'
              'depends of public opinion. The law is no protection.'),
             'expected':
             ('Your monthly update about The Point Is That the Relative '
              'Freedom W...')}]

        for test_case in data:
            self.assertEqual(
                bookmark_utils.truncate_subject(
                    'Your monthly update about ', test_case['input']),
                test_case['expected'])


def _makeContext(**kwargs):
    empty_context = {
        'most_changing': {
            'declines': [
            ],
            'improvements': [
            ]
        },
        'top_savings': {
            'possible_top_savings_total': 0.0,
            'possible_savings': [],
            'achieved_savings': []
        },
        'worst': [
        ],
        'best': [
        ],
        'most_changing_interesting': [
        ],
        'interesting': [
        ]
    }
    if 'declines' in kwargs:
        empty_context['most_changing']['declines'] = kwargs['declines']
    if 'improvements' in kwargs:
        empty_context['most_changing']['improvements'] = (
            kwargs['improvements'])
    if 'possible_top_savings_total' in kwargs:
        empty_context['top_savings']['possible_top_savings_total'] = (
            kwargs['possible_top_savings_total'])
    if 'possible_savings' in kwargs:
        empty_context['top_savings']['possible_savings'] = (
            kwargs['possible_savings'])
    if 'achieved_savings' in kwargs:
        empty_context['top_savings']['achieved_savings'] = (
            kwargs['achieved_savings'])
    if 'worst' in kwargs:
        empty_context['worst'] = kwargs['worst']
    if 'best' in kwargs:
        empty_context['best'] = kwargs['best']
    if 'interesting' in kwargs:
        empty_context['interesting'] = kwargs['interesting']
    if 'most_changing_interesting' in kwargs:
        empty_context['most_changing_interesting'] = \
          kwargs['most_changing_interesting']
    return empty_context
