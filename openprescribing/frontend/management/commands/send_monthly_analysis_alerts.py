import subprocess
import datetime
import glob
import os
from premailer import transform
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from anymail.message import attach_inline_image_file
from django.conf import settings
from django.template.loader import get_template
from django.urls import reverse
from frontend.models import SearchBookmark, User

PHANTOM = '/usr/local/bin/phantomjs'
html_email = get_template('bookmarks/email.html')


class Command(BaseCommand):
    args = ''
    help = 'Send monthly emails based on bookmarks'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        self.IS_VERBOSE = False
        if options['verbosity'] > 1:
            self.IS_VERBOSE = True
        now = datetime.datetime.now().strftime('%Y_%m_%d')
        for search_bookmark in SearchBookmark.objects.filter(
                user__is_active=True):
            target_folder = "/tmp/emails/%s/%s" % (now, search_bookmark.user.id)
            subprocess.check_call("mkdir -p %s" % target_folder, shell=True)
            cmd = ('%s %s/grab_chart.js "http://localhost:8000/analyse/#%s" %s/%s' %
                   (PHANTOM,
                    settings.SITE_ROOT + '/frontend/management/commands',
                    search_bookmark.url,
                    target_folder,
                    search_bookmark.id)
            )
            if self.IS_VERBOSE:
                print "Running " + cmd
            subprocess.check_call(cmd, shell=True)
        for user_id in os.listdir("/tmp/emails/%s" % (now)):
            user = User.objects.get(id=int(user_id))
            if self.IS_VERBOSE:
                print "Sending email to " + user.email
            bookmarks = user.searchbookmark_set.all()
            images = []
            msg = EmailMultiAlternatives(
                "Your monthly update",
                "This email is only available in HTML",
                "hello@openprescribing.net",
                [user.email])
            for image in glob.glob("/tmp/emails/%s/%s/*png" % (now, user.id)):
                images.append(attach_inline_image_file(msg, image))

            html = transform(html_email.render(
                context={
                    'images_and_bookmarks': zip(images, bookmarks),
                    'unsubscribe_link': reverse(
                        'bookmark-login',
                        key=user.profile.key)
                }))
            msg.attach_alternative(html, "text/html")

            # Optional Anymail extensions:
            msg.metadata = {"user_id": user.id, "experiment_variation": 1}
            msg.tags = ["monthly_update"]
            msg.track_clicks = True
            msg.esp_extra = {"sender_domain": "openprescribing.net"}
            sent = msg.send()
            if self.IS_VERBOSE:
                print "Sent %s messages" % sent
