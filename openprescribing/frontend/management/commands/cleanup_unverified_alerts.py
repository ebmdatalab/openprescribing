from django.utils import timezone
from dateutil.relativedelta import relativedelta
import logging

from django.core.management.base import BaseCommand
from django.db.models import Count

from frontend.models import OrgBookmark
from frontend.models import SearchBookmark
from frontend.models import User

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ''
    help = 'Remove stale bookmarks and users. Should be run daily.'

    def handle(self, *args, **options):
        now = timezone.now()
        one_month_ago = now + relativedelta(months=-1)
        OrgBookmark.objects.filter(
            created_at__lte=one_month_ago, approved=False).delete()
        SearchBookmark.objects.filter(
            created_at__lte=one_month_ago, approved=False).delete()
        deleted_users = User.objects.annotate(
            num_bookmarks=Count('orgbookmark', distinct=True) +
            Count('searchbookmark', distinct=True)
            ).filter(num_bookmarks=0,
                     emailaddress__verified=False,
                     is_superuser=False,
                     date_joined__lte=one_month_ago).delete()
        logger.info("Deleted %s user accounts & associated models" %
                     deleted_users[0])
