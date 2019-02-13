from allauth.account.utils import send_email_confirmation
from django.conf import settings
from django.core.management.base import BaseCommand
from django.test import RequestFactory

from frontend.models import User


class Command(BaseCommand):
    """Command to resend confirmation emails to unverified users with
    emails filtered by the `email_contains` option.

    The message in the confirmation emails is defined in templates at
    `account/email/email_confirmation_message`. To override the
    standard message when running this command, alter the templates in
    `openprescribing/template_overrides/` and execute this command
    with custom settings, thus:

         python manage.py resend_confirmation_emails \
           --email_contains=fred.bloggs \
           --settings=openprescribing.settings.templateoverride

    """
    def add_arguments(self, parser):
        parser.add_argument('--email_contains')
        parser.add_argument('--sent_log')

    def handle(self, *args, **options):
        users = User.objects.filter(
            emailaddress__verified=False,
            emailaddress__email__contains=options['email_contains'])
        request = RequestFactory().get('/')
        request.environ['SERVER_NAME'] = settings.ALLOWED_HOSTS[0]
        with open(options['sent_log'], 'a+') as f:
            f.seek(0)
            already_sent = set(f.read().strip().splitlines())
            for user in users:
                email = user.email
                if email in already_sent:
                    print 'Skipping', user
                    continue
                f.write(email+'\n')
                f.flush()
                print "Resending to", user
                send_email_confirmation(request, user)
