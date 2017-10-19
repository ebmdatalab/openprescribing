from sets import Set
import pandas as pd

from django.core.management.base import BaseCommand

from frontend.models import GenericCodeMapping
from frontend.models import Presentation


class Command(BaseCommand):
    args = ''
    help = 'Imports code substitutions for PPU calculations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--substitutions-csv',
            help='Path to CSV detailing Tab/Cap substitutions etc',
            type=str,
            required=True)

    def handle(self, *args, **options):
        """Handle code substitutions.

        Because (for example) Tramadol tablets and capsules can almost
        always be substituted, we consider them the same chemical for
        the purpose of our analysis.

        Therefore, wherever Tramadol capsules appear in the source data,
        we treat them as Tramadol tablets (for example).

        The mapping of what we consider equivalent is stored in a Google
        Sheet.  See https://github.com/ebmdatalab/price-per-dose/issues/11

        """
        cases = []
        seen = Set()
        df = pd.read_csv(options['substitutions_csv'])
        df = df[df['Really equivalent?'] == 'Y']
        GenericCodeMapping.objects.all().delete()
        for row in df.iterrows():
            data = row[1]
            source_code = data['Code'].strip()
            code_to_merge = data['Alternative code'].strip()
            if source_code not in seen and code_to_merge not in seen:
                cases.append((source_code, code_to_merge))
            seen.add(source_code)
            seen.add(code_to_merge)
        for to_code, from_code in cases:
            GenericCodeMapping.objects.create(
                from_code=from_code, to_code=to_code)
        for special_case in ['0601060U0', '0601060D0']:
            for from_code in Presentation.objects.filter(
                    bnf_code__startswith=special_case).values_list(
                        'bnf_code', flat=True):
                GenericCodeMapping.objects.create(
                    from_code=from_code, to_code=special_case + '%')
