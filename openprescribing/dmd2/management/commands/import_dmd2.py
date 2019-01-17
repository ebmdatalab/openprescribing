import glob
import os
from lxml import etree
from django.core.management import BaseCommand
from django.db import connection, transaction
from django.db.models import fields as django_fields

from dmd2 import models


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('data_dir')

    def handle(self, *args, **kwargs):
        self.data_dir = kwargs['data_dir']

        with transaction.atomic():
            self.import_dmd()

    def import_dmd(self):
        # lookup
        for elts in self.load_elts('lookup'):
            model_name = self.make_model_name(elts.tag)
            model = getattr(models, model_name)
            self.import_model(model, elts)

        # ingredient
        elts = self.load_elts('ingredient')
        self.import_model(models.Ing, elts)

        # vtm
        elts = self.load_elts('vtm')
        self.import_model(models.VTM, elts)

        # vmp
        for elts in self.load_elts('vmp'):
            model_name = self.make_model_name(elts[0].tag)
            model = getattr(models, model_name)
            self.import_model(model, elts)

        # vmpp
        for elts in self.load_elts('vmpp'):
            if elts[0].tag == 'CCONTENT':
                # TODO Handle CCONTENT
                continue

            model_name = self.make_model_name(elts[0].tag)
            model = getattr(models, model_name)
            self.import_model(model, elts)

        # amp
        for elts in self.load_elts('amp'):
            if len(elts) == 0:
                # TODO Shouldn't hit this with real data, so fix test data.
                continue

            model_name = self.make_model_name(elts[0].tag)
            model = getattr(models, model_name)
            self.import_model(model, elts)

        # ampp
        for elts in self.load_elts('ampp'):
            if elts[0].tag == 'CCONTENT':
                # TODO Handle CCONTENT
                continue

            if len(elts) == 0:
                # TODO Shouldn't hit this with real data, so fix test data.
                continue

            model_name = self.make_model_name(elts[0].tag)
            model = getattr(models, model_name)
            self.import_model(model, elts)

        # gtin
        elts = self.load_elts('gtin')[0]
        for elt in elts:
            assert elt[0].tag == 'AMPPID'
            assert elt[1].tag == 'GTINDATA'

            elt[0].tag = 'APPID'
            for gtinelt in elt[1]:
                elt.append(gtinelt)
            elt.remove(elt[1])
        self.import_model(models.GTIN, elts)

    def load_elts(self, obj_type):
        paths = glob.glob(os.path.join(self.data_dir, 'f_{}2_*.xml'.format(obj_type)))
        assert len(paths) == 1

        print(paths[0])

        with open(paths[0]) as f:
            doc = etree.parse(f)

        root = doc.getroot()
        elts = list(root)
        assert isinstance(elts[0], etree._Comment)
        return elts[1:]

    def import_model(self, model, elts):
        model.objects.all().delete()

        boolean_field_names = [
            f.name for f in model._meta.fields
            if isinstance(f, django_fields.BooleanField)
        ]

        table_name = model._meta.db_table
        column_names = [
            f.db_column or f.name
            for f in model._meta.fields
            if not isinstance(f, django_fields.AutoField)
        ]
        sql = 'INSERT INTO {} ({}) VALUES ({})'.format(
            table_name,
            ', '.join(column_names),
            ', '.join(['%s'] * len(column_names))
        )

        values = []

        for elt in elts:
            row = {}

            for field_elt in elt:
                name = field_elt.tag.lower()
                if name == 'desc':
                    name = 'descr'
                elif name == 'dnd':
                    name = 'dndcd'

                value = field_elt.text
                row[name] = value

            for name in boolean_field_names:
                row[name] = (name in row)

            values.append([row.get(name) for name in column_names])

        with connection.cursor() as cursor:
            cursor.executemany(sql, values)

    def make_model_name(self, table_name):
        if table_name in [
            'VTM',
            'VPI',
            'VMP',
            'VMPP',
            'AMP',
            'AMPP',
            'GTIN',
        ]:
            return table_name
        else:
            return ''.join(tok.title() for tok in table_name.split('_'))
