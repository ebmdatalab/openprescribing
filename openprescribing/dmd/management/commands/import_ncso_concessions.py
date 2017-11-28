# coding=utf8

import io
import re

from backports import csv

from django.core.management import BaseCommand

from dmd.models import NCSOConcession, DMDVmpp


def convert_ncso_name(name):
    # Some NCSO records have non-breaking spaces
    name = name.replace(u'\xa0', '')

    # Some NCSO records have multiple spaces
    name = re.sub(' +', ' ', name)

    # Some NCSO records are "(new)"
    name = name.replace(' (new)', '')

    # dm+d uses "microgram" or "micrograms", usually with these rules
    name = name.replace('mcg ', 'microgram ')
    name = name.replace('mcg/', 'micrograms/')

    # dm+d uses "microgram" rather than "0.X.mg"
    name = name.replace('0.5mg', '500microgram')
    name = name.replace('0.25mg', '250microgram')

    # dm+d uses "square cm"
    name = name.replace('sq cm', 'square cm')

    # dm+d records measured in mg/ml have a space before the final "ml"
    # eg: Abacavir 20mg/ml oral solution sugar free 240 ml
    name = re.sub(r'(\d)ml$', r'\1 ml', name)

    # dm+d records have "gram$" not "g$"
    # eg: Estriol 0.01% cream 80 gram
    name = re.sub(r'(\d)g$', r'\1 gram', name)

    # Misc.
    name = name.replace('Oral Susp SF', 'oral suspension sugar free')
    name = name.replace('gastro- resistant', 'gastro-resistant')
    name = name.replace('/ml', '/1ml')

    return name


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--filename', required=True)

    def handle(self, *args, **kwargs):
        filename = kwargs['filename']

        match = re.search('ncso_concessions_(\d{4}_\d{2}).csv', filename)
        year_and_month = match.groups()[0]

        vmpps = DMDVmpp.objects.values('nm', 'vppid')

        with io.open(filename, encoding='utf8') as f:
            fieldnames = ['drug', 'pack_size', 'price_concession']
            reader = csv.DictReader(f, fieldnames=fieldnames)

            for record in reader:
                print(record)
                match = re.match(u'£(\d+)\.(\d\d)', record['price_concession'])
                price_concession_pence = 100 * int(match.groups()[0]) \
                    + int(match.groups()[1])

                if NCSOConcession.objects.filter(
                    year_and_month=year_and_month,
                    drug=record['drug'],
                    pack_size=record['pack_size'],
                ).exists():
                    continue

                concession = NCSOConcession(
                    year_and_month=year_and_month,
                    drug=record['drug'],
                    pack_size=record['pack_size'],
                    price_concession_pence=price_concession_pence
                )

                ncso_name_raw = u'{} {}'.format(
                    record['drug'],
                    record['pack_size']
                )
                ncso_name = convert_ncso_name(ncso_name_raw)

                for vmpp in vmpps:
                    # NCSO records are inconsistent with slashes
                    vpmm_name_reg = vmpp['nm'].lower()
                    vpmm_name_reg = re.sub(' */ *', '/', vpmm_name_reg)

                    ncso_name_reg = ncso_name.lower()
                    ncso_name_reg = re.sub(' */ *', '/', ncso_name_reg)

                    if (vpmm_name_reg == ncso_name_reg or
                            vpmm_name_reg.startswith(ncso_name_reg + ' ')):

                        concession.vmpp_id = vmpp['vppid']
                        break

                else:
                    previous_concession = NCSOConcession.objects.filter(
                        drug=concession.drug,
                        pack_size=concession.pack_size,
                    ).first()

                    if previous_concession is not None:
                        concession.vmpp_id = previous_concession.vmpp_id
                    else:
                        print(u'No match found for {}'.format(ncso_name_raw))

                concession.save()
