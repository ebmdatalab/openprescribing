from django.core.management import BaseCommand
from frontend.models import ImportLog


class Command(BaseCommand):
    help = (
        "Records the fact that all data needed to render dashboards finished importing"
    )

    def handle(self, *args, **kwargs):
        date = ImportLog.objects.latest_in_category("prescribing").current_at
        ImportLog.objects.get_or_create(category="dashboard_data", current_at=date)
