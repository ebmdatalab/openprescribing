from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management import BaseCommand
from django.template.loader import get_template
from frontend.models import Practice
from gcutils.bigquery import Client


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        sql = """
        SELECT
          practice AS items
        FROM
          hscic.normalised_prescribing
        WHERE
          bnf_code LIKE '0604012U0%' AND month >= '2019-09-01'
        GROUP BY practice
        ORDER BY practice
        """

        practice_ids = [row[0] for row in Client().query(sql).rows]

        practices = Practice.objects.filter(pk__in=practice_ids)
        pcns = set(practice.pcn for practice in practices)
        ccgs = set(practice.ccg for practice in practices)

        url = "https://openprescribing.net/analyse/#org=practice&numIds=0604012U0&denom=nothing&selectedTab=chart&orgIds="

        for practice in practices:
            ctx = {"url": url + practice.code, "org_name": practice.name}

            for bm in practice.orgbookmark_set.all():
                self.send_email(bm.user.email, ctx)

        for pcn in pcns:
            if pcn is None:
                continue

            pcn_practices = practices.filter(pcn=pcn)
            ctx = {
                "url": url + ",".join(p.code for p in pcn_practices),
                "org_name": pcn.name,
            }

            for bm in pcn.orgbookmark_set.all():
                self.send_email(bm.user.email, ctx)

        for ccg in ccgs:
            if ccg is None:
                continue

            ccg_practices = practices.filter(ccg=ccg)
            ctx = {
                "url": url + ",".join(p.code for p in ccg_practices),
                "org_name": ccg.name,
            }

            for bm in ccg.orgbookmark_set.all():
                self.send_email(bm.user.email, ctx)

    def send_email(self, to_addr, ctx):
        print("Sending to:", to_addr)
        html_template = get_template("esmya.html")
        html = html_template.render(ctx)

        text_template = get_template("esmya.txt")
        text = text_template.render(ctx)

        subject = "Esmya (ulipristal acetate) - Drug Safety Alert"
        from_addr = settings.DEFAULT_FROM_EMAIL

        msg = EmailMultiAlternatives(subject, text, from_addr, [to_addr])
        msg.attach_alternative(html, "text/html")
        msg.send()
