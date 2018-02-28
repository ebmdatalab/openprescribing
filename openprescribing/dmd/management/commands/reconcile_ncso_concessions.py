from __future__ import print_function

from django.core.management import BaseCommand

from openprescribing.utils import get_input
from dmd.models import NCSOConcession, DMDVmpp
from gcutils.bigquery import Client


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        unreconciled_concessions = NCSOConcession.objects.unreconciled()
        num = unreconciled_concessions.count()

        self.stdout.write('There are {} unreconciled concessions'.format(num))
        for concession in unreconciled_concessions:
            self.handle_concession(concession)

        Client('dmd').upload_model(NCSOConcession)

    def handle_concession(self, concession):
        self.stdout.write('~' * 10)
        self.stdout.write('Unreconciled concession:')
        self.stdout.write(u'   drug: {}'.format(concession.drug))
        self.stdout.write('   pack size: {}'.format(concession.pack_size))

        while True:
            self.stdout.write('')
            self.stdout.write('Enter search term (case insensitive):')
            q = get_input()
            self.stdout.write('')

            candidates = DMDVmpp.objects.filter(nm__icontains=q).order_by('nm')

            num_candidates = candidates.count()

            if num_candidates == 0:
                self.stdout.write('Found no matching VMPPs')
                continue
            elif num_candidates == 1:
                self.stdout.write('Found 1 matching VMPP')
            else:
                self.stdout.write(
                    'Found {} matching VMPPs'.format(num_candidates))

            for ix, candidate in enumerate(candidates):
                self.stdout.write('{:>3}. {}'.format(ix + 1, candidate.nm))

            self.stdout.write('')
            self.stdout.write(
                'Enter number of matching VMPP, or 0 to search again:')

            candidate_ix = self.get_candidate_ix(num_candidates)

            if candidate_ix == 0:
                continue

            candidate = candidates[candidate_ix - 1]

            self.stdout.write('Matching against:')
            self.stdout.write('    {}'.format(candidate.nm))
            self.stdout.write('')
            self.stdout.write('Please confirm [yN]:')

            if self.get_yn():
                break

        concession.vmpp = candidate
        concession.save()

    def get_candidate_ix(self, num_candidates):
        while True:
            ix = get_input()
            try:
                ix = int(ix)
            except ValueError:
                continue

            if 0 <= ix <= num_candidates:
                return ix

    def get_yn(self):
        while True:
            yn = get_input()
            if yn.lower() == 'y':
                return True
            elif yn.lower() == 'n':
                return False
