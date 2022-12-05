import csv
import sys

from django.core.management.base import BaseCommand
from frontend.models import OrgBookmark


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        fieldnames = ["org_type", "org_code", "org_name", "email_address", "created_at"]
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()

        for bookmark in OrgBookmark.objects.order_by("created_at"):
            if bookmark.pct:
                org_type = "ccg"
                org_code = bookmark.pct.code
                org_name = bookmark.pct.name
            elif bookmark.practice:
                org_type = "practice"
                org_code = bookmark.practice.code
                org_name = bookmark.practice.name
            else:
                org_type = "all-england"
                org_code = None
                org_name = None

            row = {
                "org_type": org_type,
                "org_code": org_code,
                "org_name": org_name,
                "email_address": bookmark.user.email,
                "created_at": bookmark.created_at,
            }
            writer.writerow(row)
