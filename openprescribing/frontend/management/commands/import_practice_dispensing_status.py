import xlrd
from django.core.management.base import BaseCommand, CommandError
from frontend.models import Practice, PracticeIsDispensing as PID


class Command(BaseCommand):
    args = ''
    help = 'Imports practice dispensing status.'

    def add_arguments(self, parser):
        parser.add_argument('--filename')
        parser.add_argument('--date')

    def handle(self, *args, **options):
        self.IS_VERBOSE = False
        if options['verbosity'] > 1:
            self.IS_VERBOSE = True

        if not options['filename']:
            raise CommandError('Please supply a filename')

        if not options['date']:
            raise CommandError('Please supply a date')

        workbook = xlrd.open_workbook(options['filename'])
        worksheet = workbook.sheet_by_name('Sheet1')
        num_rows = worksheet.nrows - 1
        curr_row = -1
        name_and_postcode_matches = 0
        useful_rows = 0
        address1_and_postcode_matches = 0
        name_only_matches = 0
        postcode_only_matches = 0
        multiple_matches_found = 0

        while curr_row < num_rows:
            curr_row += 1
            address = worksheet.cell_value(curr_row, 1).strip()
            if address == 'Dispensing Practices Address Details' or \
               address == 'Primary Care Trust:' or \
               address == 'Report For:' or \
               address == 'Practice Name and Address':
                continue
            useful_rows += 1
            addresses = address.split(',')
            name = addresses[0].strip().upper()
            postcode = addresses[-1].strip().replace('\n', ' ')

            # Deal with addresses with missing postcode.
            addr_with_no_postcode = 'Old School Surgery, Church Street, '
            addr_with_no_postcode += 'Seaford, East Sussex'
            if address == addr_with_no_postcode:
                postcode = 'BN25 1HH'
            if ' ' not in postcode or len(postcode) > 8:
                print 'POSTCODE ISSUE', address

            p = None
            try:
                p = Practice.objects.get(name=name,
                                         postcode=postcode)
                name_and_postcode_matches += 1
            except Practice.DoesNotExist:
                # No match on name and postcode. Try other strategies.
                try:
                    p = Practice.objects.get(address1=name,
                                             postcode=postcode)
                    address1_and_postcode_matches += 1
                except Practice.DoesNotExist:
                    ps = Practice.objects.filter(postcode=postcode)
                    if ps:
                        # for ps1 in ps:
                        #     print 'match on postcode only'
                        #     print address
                        #     print ps1.code, ps1.name + ', ' + \
                        #        ps1.address_pretty()
                        # print ''
                        name_only_matches += 1
                    else:
                        ps = Practice.objects.filter(name=name)
                        if ps:
                            # for ps1 in ps:
                            #     print 'match on name only'
                            #     print address
                            #     print ps1.code, ps1.name + ', ' + \
                            #        ps1.address_pretty()
                            # print ''
                            postcode_only_matches += 1
                except Practice.MultipleObjectsReturned:
                    multiple_matches_found += 1
            except Practice.MultipleObjectsReturned:
                multiple_matches_found += 1

            if p:
                pds, created = PID.objects.get_or_create(practice=p,
                                                         date=options['date'])

        # print useful_rows, 'rows'
        # print address1_and_postcode_matches, 'address1_and_postcode_matches'
        # print name_only_matches, 'name_only_matches'
        # print postcode_only_matches, 'postcode_only_matches'
        # total_matches = name_and_postcode_matches
        # total_matches += address1_and_postcode_matches + name_only_matches
        # total_matches += postcode_only_matches
        # print useful_rows - (total_matches), ' no matches'
