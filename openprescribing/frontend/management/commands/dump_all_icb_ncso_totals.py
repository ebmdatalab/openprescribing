import csv
import sys
from datetime import date

from django.core.management.base import BaseCommand
from frontend.models import STP, NCSOConcession, TariffPrice
from frontend.views.spending_utils import (
    _get_concession_cost_matrices,
    numpy,
)
from matrixstore.db import get_db


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        writer = csv.DictWriter(
            sys.stdout,
            fieldnames=[
                "org_code",
                "org_name",
                "month",
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
        price_months = sorted(tariff_months & ncso_months)
        prescribing_months = [date.fromisoformat(d) for d in get_db().dates]
        target_months = [
            m
            for m in price_months
            if m in prescribing_months or m > prescribing_months[-1]
        ]

        start_date = target_months[0]
        end_date = target_months[-1]

        for org in all_orgs:
            org_name = org.name.replace("INTEGRATED CARE BOARD", "").strip()
            breakdown = ncso_spending_breakdown(
                org_type, org.code, start_date, end_date
            )
            for row in breakdown:
                writer.writerow(
                    {
                        "org_code": org.code,
                        "org_name": org_name,
                        "month": row[0],
                        "tariff_cost": f"{row[1]:.2f}",
                        "extra_cost": f"{row[2]:.2f}",
                        "is_estimate": row[0] not in prescribing_months,
                    }
                )


def ncso_spending_breakdown(org_type, org_id, start_date, end_date):
    costs = _get_concession_cost_matrices(start_date, end_date, org_type, org_id)
    # Sum together costs over all presentations (i.e. all rows)
    tariff_costs = numpy.sum(costs.tariff_costs, axis=0)
    extra_costs = numpy.sum(costs.extra_costs, axis=0)
    for date_str, offset in sorted(costs.date_offsets.items()):
        if extra_costs[offset] == 0:
            continue
        yield (
            date.fromisoformat(date_str),
            float(tariff_costs[offset]),
            float(extra_costs[offset]),
        )
