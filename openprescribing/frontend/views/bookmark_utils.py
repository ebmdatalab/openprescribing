# -*- coding: utf-8 -*-
from datetime import date
from tempfile import NamedTemporaryFile
import HTMLParser
import logging
import re
import subprocess
import urllib
import urlparse

from anymail.message import attach_inline_image_file
from dateutil.relativedelta import relativedelta
from premailer import Premailer
import numpy as np

from django.conf import settings
from django.contrib.humanize.templatetags.humanize import apnumber
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.template.loader import get_template
from django.utils.safestring import mark_safe

from frontend.models import ImportLog
from frontend.models import Measure
from frontend.models import MeasureValue

GRAB_CMD = ('/usr/local/bin/phantomjs ' +
            settings.SITE_ROOT +
            '/frontend/management/commands/grab_chart.js')

logger = logging.getLogger(__name__)


def remove_jagged(measurevalues):
    """Remove records that are outside the standard error of the mean or
    where they hit 0% or 100% more than once.

    Bit of a guess as to if this'll work or not. Pending review by
    real statistician.

    """
    values = [x.percentile for x in measurevalues]
    sem = (np.std(values) /
           np.sqrt(len(values)))
    keep = []
    extremes = 0
    for x in measurevalues:
        if x.measure.is_percentage:
            if x.calc_value == 1.0:
                extremes += 1
        if x.calc_value == 0.0:
            extremes += 1
        if x.numerator and x.numerator < 15:
            extremes += 1
        if extremes > 1 or x.percentile < sem or x.percentile > (100 - sem):
            next
        else:
            keep.append(x)
    return keep


def remove_jagged_logit(measurevalues):
    """Remove records that are outside the standard error of the mean.

    Bit of a guess as to if this'll work or not. Pending review by
    real statistivcian.

    """
    values = []
    for m in measurevalues:
        val = m.percentile / 100.0
        if val > 0 and val < 1:
            values.append(np.log(val/(100-val)))
        else:
            values.append(
                np.log(
                    (val + 0.5/len(measurevalues)) /
                    (1 - val + (0.5/len(measurevalues)))
                )
            )
    sem = (np.std(values) /
           np.sqrt(len(values)))
    keep = []
    for m in measurevalues:
        if m.percentile < sem or m.percentile > (100 - sem):
            next
        else:
            keep.append(m)
    return keep


class InterestingMeasureFinder(object):
    def __init__(self, practice=None, pct=None,
                 interesting_saving=1000,
                 interesting_percentile_change=10):
        assert practice or pct
        self.practice = practice
        self.pct = pct
        self.interesting_percentile_change = interesting_percentile_change
        self.interesting_saving = interesting_saving

    def months_ago(self, period):
        now = ImportLog.objects.latest_in_category('prescribing').current_at
        return now + relativedelta(months=-(period-1))

    def _best_or_worst_performing_in_period(self, period, best_or_worst=None):
        assert best_or_worst in ['best', 'worst']
        worst = []
        for measure in Measure.objects.all():
            measure_filter = {
                'measure': measure, 'month__gte': self.months_ago(period)}
            if self.practice:
                measure_filter['practice'] = self.practice
            else:
                measure_filter['pct'] = self.pct
                measure_filter['practice'] = None
            invert_percentile_for_comparison = False
            if measure.low_is_good:
                if best_or_worst == 'worst':
                    invert_percentile_for_comparison = True
                    measure_filter['percentile__gte'] = 90
                else:
                    measure_filter['percentile__lte'] = 10
            else:
                if best_or_worst == 'worst':
                    measure_filter['percentile__lte'] = 10
                else:
                    invert_percentile_for_comparison = True
                    measure_filter['percentile__gte'] = 90
            is_worst = remove_jagged(
                MeasureValue.objects.filter(**measure_filter))
            if len(is_worst) == period:
                if invert_percentile_for_comparison:
                    comparator = 100 - is_worst[-1].percentile
                else:
                    comparator = is_worst[-1].percentile
                worst.append((measure, comparator))
        worst = sorted(worst, key=lambda x: x[-1])
        return [x[0] for x in worst]

    def worst_performing_in_period(self, period):
        """Return every measure where the organisation specified in the given
        bookmark is in the worst decile for each month in the
        specified time range

        """
        return self._best_or_worst_performing_in_period(period, 'worst')

    def best_performing_in_period(self, period):
        """Return every measure where organisations specified in the given
        bookmark is in the best decile for each month in the specified
        time range

        """
        return self._best_or_worst_performing_in_period(period, 'best')

    def most_change_in_period(self, period):
        """Every measure where the specified organisation has changed by more
        than 10 centiles in the specified time period, ordered by rate
        of change.

        The rate of change is worked out using a line of best fit.

        Returns a list of triples of (measure, change_from, change_to)

        """
        improvements = []
        declines = []
        for measure in Measure.objects.all():
            measure_filter = {
                'measure': measure,
                'month__gte': self.months_ago(period),
                'percentile__isnull': False
            }
            if self.practice:
                measure_filter['practice'] = self.practice
            else:
                measure_filter['pct'] = self.pct
                measure_filter['practice'] = None
            percentiles = [x.percentile for x in
                           remove_jagged(
                               MeasureValue.objects.filter(**measure_filter)
                               .order_by('month'))]
            if len(percentiles) == period:
                x = np.arange(period)
                y = np.array(percentiles)
                p, res, _, _, _ = np.polyfit(x, y, 1, full=True)
                m, b = p
                residuals = res[0]
                start_centile = b
                end_centile = m * (period - 1) + b
                if residuals < 1200:
                    delta = start_centile - end_centile
                    data = (m, measure, start_centile,
                            end_centile, residuals)
                    if delta >= self.interesting_percentile_change:
                        if measure.low_is_good:
                            improvements.append(data)
                        else:
                            declines.append(data)
                    elif delta <= (0 - self.interesting_percentile_change):
                        if measure.low_is_good:
                            declines.append(data)
                        else:
                            improvements.append(data)

        improvements = sorted(improvements, key=lambda x: -abs(x[0]))
        declines = sorted(declines, key=lambda x: -abs(x[0]))
        return {'improvements': [d[1:] for d in improvements],
                'declines': [d[1:] for d in declines]}

    def top_and_total_savings_in_period(self, period):
        """Sum total possible savings over time, and find measures where
        possible or achieved savings are greater than self.interesting_saving.

        Returns a dictionary where the keys are
        `possible_top_savings_total`, `possible_savings` and
        `achieved_savings`; and the values are an integer, sorted
        `(measure, saving)` tuples, and sorted `(measure, saving)`
        tuples respectively.

        """
        possible_savings = []
        achieved_savings = []
        total_savings = 0
        for measure in Measure.objects.all():
            if measure.is_cost_based:
                measure_filter = {
                    'measure': measure, 'month__gte': self.months_ago(period)}
                if self.practice:
                    measure_filter['practice'] = self.practice
                else:
                    measure_filter['pct'] = self.pct
                    measure_filter['practice'] = None
                values = list(
                    MeasureValue.objects.filter(**measure_filter))
                if len(values) != period:
                    continue
                savings_at_50th = [
                    x.cost_savings['50'] for x in
                    values]
                savings_or_loss_for_measure = sum(savings_at_50th)
                if savings_or_loss_for_measure >= self.interesting_saving:
                    possible_savings.append(
                        (measure, savings_or_loss_for_measure)
                    )
                if savings_or_loss_for_measure <= -self.interesting_saving:
                    achieved_savings.append(
                        (measure, -1 * savings_or_loss_for_measure))
                if measure.low_is_good:
                    savings_at_10th = sum([
                        max(0, x.cost_savings['10']) for x in
                        values])
                else:
                    savings_at_10th = sum([
                        max(0, x.cost_savings['90']) for x in
                        values])
                total_savings += savings_at_10th
        return {
            'possible_savings': sorted(
                possible_savings, key=lambda x: -x[1]),
            'achieved_savings': sorted(
                achieved_savings, key=lambda x: x[1]),
            'possible_top_savings_total': total_savings
        }

    def context_for_org_email(self):
        return {
            'worst': self.worst_performing_in_period(3),
            'best': self.best_performing_in_period(3),
            'most_changing': self.most_change_in_period(9),
            'top_savings': self.top_and_total_savings_in_period(6)}


def attach_image(msg, url, file_path, selector, dimensions='1024x1024'):
    if 'selectedTab=map' in url:
        wait = 8000
        dimensions = '1000x600'
    elif 'selectedTab=chart' in url:
        wait = 1000
        dimensions = '800x600'
    elif 'selectedTab' in url:
        wait = 500
        dimensions = '800x600'
    else:
        wait = 500
    cmd = '{cmd} "{host}{url}" {file_path} "{selector}" {dimensions} {wait}'
    cmd = (
        cmd.format(
            cmd=GRAB_CMD,
            host=settings.GRAB_HOST,
            url=url,
            file_path=file_path,
            selector=selector,
            dimensions=dimensions,
            wait=wait
        )
    )
    result = subprocess.check_output(cmd, shell=True)
    logger.debug("Command %s completed with output %s" % (cmd, result.strip()))
    return attach_inline_image_file(
        msg, file_path, subtype='png')


def getIntroText(stats, org_type):
    declines = len(stats['most_changing']['declines'])
    improvements = len(stats['most_changing']['improvements'])
    possible_savings = len(stats['top_savings']['possible_savings'])
    worst = len(stats['worst'])
    best = len(stats['best'])
    not_great = worst + declines
    pretty_good = best + improvements
    msg = ""
    in_sentence = False
    if not_great or pretty_good or possible_savings:
        if not_great:
            msg = "We've found %s prescribing measure%s where this %s " % (
                apnumber(not_great),
                not_great > 1 and 's' or '',
                org_type)
            in_sentence = True
            if declines and worst:
                msg += "<span class='worse'>is getting worse, or could be "
                msg += "doing better</span>"
            elif declines:
                msg += "<span class='worse'>is getting worse</span>"
            else:
                msg += "<span class='worse'>could be doing better</span>"
        else:
            msg = ("Good news: we've not found any problem prescribing "
                   "measures for this %s!" % org_type)
            in_sentence = False
        if pretty_good:
            if msg and in_sentence:
                msg += ", and %s measure%s where it " % (
                    apnumber(pretty_good),
                    pretty_good > 1 and 's' or '')
            else:
                msg = ("We've found %s prescribing measure%s where "
                       "this %s " % (apnumber(pretty_good),
                                     pretty_good > 1 and 's' or '',
                                     org_type))
            if best and improvements:
                msg += "<span class='better'>is doing well</span>."
            elif improvements:
                msg += "<span class='better'>is improving</span>."
            else:
                msg += "<span class='better'>is already doing "
                msg += "very well</span>."
            in_sentence = False
        if in_sentence:
            msg += ". "
        if possible_savings:
            if msg:
                msg += " We've also found "
            else:
                msg = "We've found "
            msg += ("%s prescribing measure%s where there are some "
                    "potential cost savings." % (
                        apnumber(possible_savings),
                        possible_savings > 1 and 's' or ''))
    else:
        msg = ("We've no new information about this %s this month! "
               "Its performance is not an outlier on any "
               "of our common prescribing measures." % org_type)
    return mark_safe(msg)


def _hasStats(stats):
    return (stats['worst'] or
            stats['best'] or
            stats['top_savings']['possible_top_savings_total'] or
            stats['top_savings']['possible_savings'] or
            stats['top_savings']['achieved_savings'] or
            stats['most_changing']['declines'] or
            stats['most_changing']['improvements'])


def ga_tracking_qs(context):
    tracking_params = {
        'utm_medium': 'email',
        'utm_campaign': context['campaign_name'],
        'utm_source': context['campaign_source'],
        'utm_content': context['email_id']
    }
    return urllib.urlencode(tracking_params)


def truncate_subject(prefix, subject):
    assert subject, "Subject must not be empty"
    max_length = 78 - len(prefix) - len(settings.EMAIL_SUBJECT_PREFIX)
    ellipsis = '...'
    subject = subject[0].lower() + subject[1:]
    if len(subject) <= max_length:
        truncated = subject
    else:
        if 'by' in subject:
            end_bit = subject.split('by')[-1]
            end_bit = 'by' + end_bit
        else:
            end_bit = ''
        start_bit = subject[:(max_length - len(end_bit) - len(ellipsis))]
        truncated = start_bit + ellipsis + end_bit
    return prefix + truncated


def make_email_with_campaign(bookmark, campaign_source):
    campaign_name = "monthly alert %s" % date.today().strftime("%Y-%m-%d")
    email_id = "/email/%s/%s/%s" % (
        campaign_name,
        campaign_source,
        bookmark.id)
    subject_prefix = 'Your monthly update about '
    msg = EmailMultiAlternatives(
        truncate_subject(subject_prefix, bookmark.name),
        "This email is only available in HTML",
        settings.SUPPORT_EMAIL,
        [bookmark.user.email])
    metadata = {"subject": msg.subject,
                "campaign_name": campaign_name,
                "campaign_source": campaign_source,
                "email_id": email_id}
    msg.metadata = metadata
    msg.qs = ga_tracking_qs(metadata)
    return msg


def make_org_email(org_bookmark, stats):
    msg = make_email_with_campaign(org_bookmark, 'dashboard-alerts')
    dashboard_uri = (
        settings.GRAB_HOST + org_bookmark.dashboard_url() +
        '?' + msg.qs)
    html_email = get_template('bookmarks/email_for_measures.html')
    with NamedTemporaryFile(suffix='.png') as getting_worse_file, \
            NamedTemporaryFile(suffix='.png') as still_bad_file:
        most_changing = stats['most_changing']
        getting_worse_img = still_bad_img = None
        if most_changing['declines']:
            getting_worse_img = attach_image(
                msg,
                org_bookmark.dashboard_url(),
                getting_worse_file.name,
                '#' + most_changing['declines'][0][0].id
            )
        if stats['worst']:
            still_bad_img = attach_image(
                msg,
                org_bookmark.dashboard_url(),
                still_bad_file.name,
                '#' + stats['worst'][0].id)
        html = html_email.render(
            context={
                'intro_text': getIntroText(
                    stats, org_bookmark.org_type()),
                'total_possible_savings': sum(
                    [x[1] for x in
                     stats['top_savings']['possible_savings']]),
                'has_stats': _hasStats(stats),
                'domain': settings.GRAB_HOST,
                'measures_count': Measure.objects.count(),
                'getting_worse_image': getting_worse_img,
                'still_bad_image': still_bad_img,
                'bookmark': org_bookmark,
                'dashboard_uri': mark_safe(dashboard_uri),
                'qs': mark_safe(msg.qs),
                'stats': stats,
                'unsubscribe_link': settings.GRAB_HOST + reverse(
                    'bookmark-login',
                    kwargs={'key': org_bookmark.user.profile.key})
            })
        html = Premailer(
            html, cssutils_logging_level=logging.ERROR).transform()
        html = unescape_href(html)
        msg.attach_alternative(html, "text/html")
        msg.tags = ["monthly_update", "measures"]
        return msg


def make_search_email(search_bookmark):
    msg = make_email_with_campaign(search_bookmark, 'analyse-alerts')
    html_email = get_template('bookmarks/email_for_searches.html')
    parsed_url = urlparse.urlparse(search_bookmark.dashboard_url())
    if parsed_url.query:
        qs = '?' + parsed_url.query + '&' + msg.qs
    else:
        qs = '?' + msg.qs
    dashboard_uri = (
        settings.GRAB_HOST + parsed_url.path + qs + '#' + parsed_url.fragment)
    with NamedTemporaryFile(suffix='.png') as graph_file:
        graph = attach_image(
            msg,
            search_bookmark.dashboard_url(),
            graph_file.name,
            '#results .tab-pane.active'
        )
        html = html_email.render(
            context={
                'bookmark': search_bookmark,
                'domain': settings.GRAB_HOST,
                'graph': graph,
                'dashboard_uri': mark_safe(dashboard_uri),
                'unsubscribe_link': settings.GRAB_HOST + reverse(
                    'bookmark-login',
                    kwargs={'key': search_bookmark.user.profile.key})
            })
        html = Premailer(
            html, cssutils_logging_level=logging.ERROR).transform()
        html = unescape_href(html)
        msg.attach_alternative(html, "text/html")
        msg.tags = ["monthly_update", "analyse"]
        return msg


def unescape_href(text):
    """Unfortunately, premailer escapes hrefs and there's [not much we can
    do about it](https://github.com/peterbe/premailer/issues/72).
    Unencode them again."""
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', text)
    html_parser = HTMLParser.HTMLParser()
    for href in hrefs:
        text = text.replace(href, html_parser.unescape(href))
    return text
