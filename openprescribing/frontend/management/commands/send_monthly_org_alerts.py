import subprocess
from tempfile import NamedTemporaryFile
from premailer import transform
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from anymail.message import attach_inline_image_file
from django.conf import settings
from django.template.loader import get_template
from django.core.urlresolvers import reverse
from frontend.models import OrgBookmark
from frontend.views import bookmark_utils


GRAB_CMD = ('/usr/local/bin/phantomjs ' +
            settings.SITE_ROOT +
            ' /frontend/management/commands/grab_chart.js')
GRAB_HOST = "https://openprescring.net"
html_email = get_template('bookmarks/email_for_measures.html')


class Command(BaseCommand):
    args = ''
    help = 'Send monthly emails based on bookmarks'

    def add_arguments(self, parser):
        parser.add_argument('--email')
        parser.add_argument('--ccg')
        parser.add_argument('--practice')

    def handle(self, *args, **options):
        recipient_email = None
        recipient_key = None
        recipient_id = None

        if options['email']:
            bookmarks = [OrgBookmark(
                pct_id=options['ccg'],
                practice_id=options['practice']
            )]
            recipient_email = options['email']
            recipient_id = 'test'
            recipient_key = 'test'
        else:
            bookmarks = OrgBookmark.objects.filter(
                user__is_active=True)
        # First, generate the images for each email
        for org_bookmark in bookmarks:

            stats = bookmark_utils.InterestingMeasureFinder(
                practice=org_bookmark.practice or options['practice'],
                pct=org_bookmark.pct or options['ccg']).context_for_org_email()
            if recipient_email is None:
                recipient_email = org_bookmark.user.email
                recipient_key = org_bookmark.user.profile.key
                recipient_id = org_bookmark.user.id
            msg = EmailMultiAlternatives(
                "Your monthly update",
                "This email is only available in HTML",
                "hello@openprescribing.net",
                [recipient_email])
            images = []
            with NamedTemporaryFile() as getting_worse_img, \
                    NamedTemporaryFile() as still_bad_img:
                most_changing = stats['most_changing']
                if most_changing['declines']:
                    getting_worse_measure = most_changing['declines'][0][0]
                    cmd = ('{cmd} "{host}{url} {file_path} #{selector}'.format(
                        cmd=GRAB_CMD,
                        host=GRAB_HOST,
                        url=org_bookmark.dashboard_url(),
                        file_path=getting_worse_img.name,
                        selector=getting_worse_measure)
                    )
                    subprocess.check_call(cmd, shell=True)
                    images.append(attach_inline_image_file(
                        msg, getting_worse_img.name))
                if stats['worst']:
                    still_bad_measure = stats['worst'][0]
                    cmd = ('{cmd} "{host}{url} {file_path} #{selector}'.format(
                        cmd=GRAB_CMD,
                        host=GRAB_HOST,
                        url=org_bookmark.dashboard_url(),
                        file_path=still_bad_img.name,
                        selector=still_bad_measure)
                    )
                    subprocess.check_call(cmd, shell=True)
                    images.append(attach_inline_image_file(
                        msg, still_bad_img.name))

                html = transform(html_email.render(
                    context={
                        'getting_worse_image': images and images[0],
                        'still_bad_img': images and images[1],
                        'bookmark': org_bookmark,
                        'stats': stats,
                        'unsubscribe_link': reverse(
                            'bookmark-login',
                            kwargs={'key': recipient_key})
                    }))
                msg.attach_alternative(html, "text/html")

                # Optional Anymail extensions:
                msg.metadata = {"user_id": recipient_id,
                                "experiment_variation": 1}
                msg.tags = ["monthly_update"]
                msg.track_clicks = True
                msg.esp_extra = {"sender_domain": "openprescribing.net"}
                sent = msg.send()
                print "Sent %s messages" % sent
