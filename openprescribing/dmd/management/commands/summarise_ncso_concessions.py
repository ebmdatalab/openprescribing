from datetime import date

from django.core.management import BaseCommand

from dmd.models import NCSOConcession


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        today = date.today()
        first_of_month = date(today.year, today.month, 1)

        num_concessions = NCSOConcession.objects.count()
        num_concessions_in_this_month = NCSOConcession.objects.filter(
            date=first_of_month
        ).count()
        unmatched_concessions = NCSOConcession.objects.filter(vmpp_id__isnull=True)
        num_unmatched_concessions = unmatched_concessions.count()

        lines = []

        lines.append("There are {} concessions".format(num_concessions))
        lines.append(
            "There are {} concessions for {}".format(
                num_concessions_in_this_month, today.strftime("%B %Y")
            )
        )

        if num_unmatched_concessions == 0:
            lines.append("There are no unreconciled concessions")
        elif num_unmatched_concessions == 1:
            lines.append("There is 1 unreconciled concession")
        else:
            lines.append(
                "There are {} unreconciled concessions".format(
                    num_unmatched_concessions
                )
            )

        if num_unmatched_concessions > 0:
            lines.append("")
            lines.append("To reconcile, tell ebmbot:")
            lines.append("`op ncso reconcile concession [ID] against vmpp [VMPP ID]`")

        for c in unmatched_concessions:
            lines.append("-" * 80)
            lines.append("ID: {}".format(c.id))
            lines.append(u"Drug: {}".format(c.drug))
            lines.append(u"Pack size: {}".format(c.pack_size))

        print("\n".join(lines))
