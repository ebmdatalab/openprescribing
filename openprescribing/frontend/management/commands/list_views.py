import glob
import os

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        fpath = os.path.dirname(__file__)
        view_paths = glob.glob(os.path.join(fpath, "./views_sql/*.sql"))
        for view in view_paths:
            print os.path.basename(view).replace('.sql', '')
