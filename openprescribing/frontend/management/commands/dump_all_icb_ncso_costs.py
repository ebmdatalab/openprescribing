import csv
import sys
from datetime import date

from django.core.management.base import BaseCommand

from frontend.models import STP, NCSOConcession, TariffPrice
from frontend.views.spending_utils import ncso_spending_breakdown_for_entity
from matrixstore.db import get_db


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        writer = csv.DictWriter(
            sys.stdout,
            fieldnames=[
                "month",
                "org_code",
                "org_name",
                "bnf_code",
                "product_name",
                "quantity",
                "tariff_cost",
                "extra_cost",
                "is_estimate",
            ],
        )
        writer.writeheader()

        all_orgs = list(STP.objects.all())
        org_type = "stp"

        tariff_months = set(
            m.replace(day=1)
            for m in TariffPrice.objects.distinct().values_list("date", flat=True)
        )
        ncso_months = set(
            [
                m.replace(day=1)
                for m in NCSOConcession.objects.distinct().values_list(
                    "date", flat=True
                )
            ]
        )
        price_months = sorted(tariff_months & ncso_months)[-24:]
        prescribing_months = [date.fromisoformat(d) for d in get_db().dates]
        target_months = [
            m
            for m in price_months
            if m in prescribing_months or m > prescribing_months[-1]
        ]

        for month in reversed(target_months):
            is_estimate = month not in prescribing_months
            for org in all_orgs:
                org_name = org.name.replace("INTEGRATED CARE BOARD", "").strip()
                breakdown = ncso_spending_breakdown_for_entity(org, org_type, month)
                for row in breakdown:
                    writer.writerow(
                        {
                            "month": month,
                            "org_code": org.code,
                            "org_name": org_name,
                            "bnf_code": row[0],
                            "product_name": row[1],
                            "quantity": row[2],
                            "tariff_cost": f"{row[3]:.2f}",
                            "extra_cost": f"{row[4]:.2f}",
                            "is_estimate": is_estimate,
                        }
                    )
