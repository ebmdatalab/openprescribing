from allauth.account.utils import send_email_confirmation
from django.conf import settings
from django.core.management.base import BaseCommand
from django.test import RequestFactory

from frontend.models import User


class Command(BaseCommand):
    """Command to resend confirmation emails to unverified users with
    emails filtered by the `email_contains` option.

    The message in the confirmation emails is defined in XXX

    """
    def add_arguments(self, parser):
        parser.add_argument('--email_contains')

    def handle(self, *args, **options):
        users = User.objects.filter(
            emailaddress__verified=False,
            emailaddress__email__contains=options['email_contains'])
        request = RequestFactory().get('/')
        request.environ['SERVER_NAME'] = settings.ALLOWED_HOSTS[0]
        for user in users:
            print "Resending to", user
            send_email_confirmation(request, user)
