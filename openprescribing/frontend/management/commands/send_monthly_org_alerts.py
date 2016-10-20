import subprocess
import logging
from tempfile import NamedTemporaryFile
from premailer import Premailer
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.contrib import humanize
from anymail.message import attach_inline_image_file
from django.conf import settings
from django.template.loader import get_template
from django.core.urlresolvers import reverse
from frontend.models import OrgBookmark
from frontend.models import User
from frontend.models import Profile

from frontend.models import OrgBookmark
from frontend.views import bookmark_utils


GRAB_CMD = ('/usr/local/bin/phantomjs ' +
            settings.SITE_ROOT +
            '/frontend/management/commands/grab_chart.js')
html_email = get_template('bookmarks/email_for_measures.html')


class Command(BaseCommand):
    args = ''
    help = ''' Send monthly emails based on bookmarks. With no arguments, sends
    an email to every user for each of their bookmarks, for the
    current month. With arguments, sends a test email to the specified
    user for the specified organisation.'''

    def add_arguments(self, parser):
        parser.add_argument('--recipient-email')
        parser.add_argument('--ccg')
        parser.add_argument('--practice')

    def get_bookmarks(self, **options):
        if 'recipient_email' in options:
            dummy_user = User(email=options['recipient_email'], id='dummyid')
            dummy_user.profile = Profile(key='dummykey')
            bookmarks = [OrgBookmark(
                user=dummy_user,
                pct_id=options['ccg'],
                practice_id=options['practice']
            )]
        else:
            # XXX add a constraint here to ensure we don't send two
            # emails for one month.
            bookmarks = OrgBookmark.objects.filter(
                user__is_active=True)
        return bookmarks

    def attach_image(self, msg, url, file_path, selector):
        cmd = ('{cmd} "{host}{url}" {file_path} "#{selector}"'.format(
            cmd=GRAB_CMD,
            host=settings.GRAB_HOST,
            url=url,
            file_path=file_path,
            selector=selector)
        )
        subprocess.check_call(cmd, shell=True)
        return attach_inline_image_file(
            msg, file_path, subtype='png')


    def handle(self, *args, **options):
        # First, generate the images for each email
        for org_bookmark in self.get_bookmarks(**options):
            stats = bookmark_utils.InterestingMeasureFinder(
                practice=org_bookmark.practice or options['practice'],
                pct=org_bookmark.pct or options['ccg']).context_for_org_email()
            recipient_email = org_bookmark.user.email
            recipient_key = org_bookmark.user.profile.key
            recipient_id = org_bookmark.user.id
            msg = EmailMultiAlternatives(
                "Your monthly update",
                "This email is only available in HTML",
                "hello@openprescribing.net",
                [recipient_email])
            getting_worse_img = still_bad_img = None
            with NamedTemporaryFile(suffix='.png') as getting_worse_img, \
                    NamedTemporaryFile(suffix='.png') as still_bad_img:
                most_changing = stats['most_changing']
                if most_changing['declines']:
                    getting_worse_measure = most_changing['declines'][0][0].id
                    getting_worse_img = self.attach_image(
                        msg,
                        org_bookmark.dashboard_url(),
                        getting_worse_img.name,
                        getting_worse_measure
                    )
                if stats['worst']:
                    still_bad_measure = stats['worst'][0].id
                    still_bad_img = self.attach_image(
                        msg,
                        org_bookmark.dashboard_url(),
                        still_bad_img.name,
                        still_bad_measure)
                html = html_email.render(
                    context={
                        'intro_text': self._getIntroText(stats),
                        'total_possible_savings': sum(
                            [x[1] for x in
                             stats['top_savings']['possible_savings']]),
                        'has_stats': self._hasStats(stats),
                        'getting_worse_image': getting_worse_img,
                        'still_bad_image': still_bad_img,
                        'bookmark': org_bookmark,
                        'stats': stats,
                        'unsubscribe_link': reverse(
                            'bookmark-login',
                            kwargs={'key': recipient_key})
                    })
                html = Premailer(html, cssutils_logging_level=logging.ERROR).transform()
                msg.attach_alternative(html, "text/html")

                # Optional Anymail extensions:
                msg.metadata = {"user_id": recipient_id,
                                "experiment_variation": 1}
                msg.tags = ["monthly_update"]
                msg.track_clicks = True
                msg.esp_extra = {"sender_domain": "openprescribing.net"}
                sent = msg.send()
                print "Sent %s messages" % sent

    def _getIntroText(self, stats):
        attention_areas = (len(stats['most_changing']['declines']) +
                           len(stats['worst']) +
                           len(stats['top_savings']['possible_savings']))
        good_areas = (len(stats['best']) +
                      len(stats['most_changing']['improvements']))
        msg = "We've found "
        if good_areas and attention_areas:
            msg += "some good news, and some areas for you to look at "
        elif good_areas:
            msg += "some good news to let you know about"
        elif attention_areas:
            msg += "some areas for you to look at"
        msg += ":"
        return msg


    def _hasStats(self, stats):
        return (stats['worst'] or
                stats['best'] or
                stats['top_savings']['possible_top_savings_total'] or
                stats['top_savings']['possible_savings'] or
                stats['top_savings']['achieved_savings'] or
                stats['most_changing']['declines'] or
                stats['most_changing']['improvements'])
