import csv
from django.core.management.base import BaseCommand, CommandError
from frontend.models import Section, Product, Presentation


class Command(BaseCommand):
    args = ''
    help = 'Imports BNF chapter, section and paragraph codes.'

    def add_arguments(self, parser):
        parser.add_argument('--filename')

    def handle(self, *args, **options):
        '''
        Import BNF numbered chapters, sections and paragraphs.
        '''
        if 'filename' not in options:
            print 'Please supply a filename'
            sys.exit

        reader = csv.DictReader(open(options['filename'], 'rU'))

        sections = {}
        for row in reader:
            product_name = row['BNF Product'].strip()
            product_code = row['BNF Product Code'].strip()
            if product_name != 'DUMMY PRODUCT':
                p, c = Product.objects.get_or_create(bnf_code=product_code,
                                                     name=product_name)

            pres_name = row['BNF Presentation'].strip()
            pres_code = row['BNF Presentation Code'].strip()
            if len(pres_code) == 15:
                p, c = Presentation.objects.get_or_create(bnf_code=pres_code,
                                                          name=pres_name)

            # Add to sections list.
            c_id = row['BNF Chapter Code']
            if c_id not in sections:
                sections[c_id] = {
                    'id': c_id,
                    'name': row['BNF Chapter']
                }
            s_id = row['BNF Section Code']
            if s_id not in sections:
                sections[s_id] = {
                    'id': s_id,
                    'name': row['BNF Section']
                }
            p_id = row['BNF Paragraph Code']
            if p_id not in sections:
                sections[p_id] = {
                    'id': p_id,
                    'name': row['BNF Paragraph']
                }

        for s in sections:
            id = sections[s]['id'].strip()
            name = sections[s]['name']
            bnf_chapter = id[:2]
            bnf_section = id[2:4]
            bnf_para = id[4:6]
            bnf_subpara = id[6:8]
            bnf_section = self.convert_bnf_id_section(bnf_section)
            bnf_para = self.convert_bnf_id_section(bnf_para)
            if self.is_valid_section(id, name, bnf_para, bnf_subpara):
                section, created = Section.objects.get_or_create(
                    bnf_id=id,
                    name=name,
                    bnf_chapter=bnf_chapter,
                    bnf_section=bnf_section,
                    bnf_para=bnf_para
                )

    def convert_bnf_id_section(self, id):
        if id == '':
            return None
        else:
            return int(id)

    def is_valid_section(self, id, name, bnf_para, bnf_subpara):
        '''
        Check for duplicate or dummy sections.
        '''
        if name.lower().startswith('dummy') or id[-2:] == '00' or \
           bnf_para == '0' or bnf_subpara == '0':
            return False
        return True
