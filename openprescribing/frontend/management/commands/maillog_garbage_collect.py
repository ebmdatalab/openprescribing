from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Max
from frontend.models import EmailMessage, MailLog


class Command(BaseCommand):
    help = "Deletes old EmailMessage instances and their associated MailLog instances."

    def handle(self, *args, **options):
        latest = EmailMessage.objects.aggregate(Max("created_at"))["created_at__max"]
        if latest is None:
            return
        threshold = latest - timedelta(days=2 * 31)
        MailLog.objects.filter(message__created_at__lt=threshold).delete()
        MailLog.objects.filter(message__isnull=True, timestamp__lt=threshold).delete()
        EmailMessage.objects.filter(created_at__lt=threshold).delete()
