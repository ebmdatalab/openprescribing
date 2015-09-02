# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Chapter',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Chemical',
            fields=[
                ('bnf_code', models.CharField(max_length=9, serialize=False, primary_key=True, validators=[django.core.validators.RegexValidator(b'^[\\w]*$', message=b'name must be alphanumeric', code=b'Invalid name')])),
                ('chem_name', models.CharField(max_length=200)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Paragraph',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PCT',
            fields=[
                ('code', models.CharField(help_text=b'Primary care trust code', max_length=3, serialize=False, primary_key=True)),
                ('ons_code', models.CharField(max_length=9, null=True, blank=True)),
                ('name', models.CharField(max_length=200, null=True, blank=True)),
                ('boundary', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True)),
                ('org_type', models.CharField(default=b'Unknown', max_length=9, choices=[(b'CCG', b'CCG'), (b'PCT', b'PCT'), (b'Unknown', b'Unknown')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Practice',
            fields=[
                ('code', models.CharField(help_text=b'Practice code', max_length=6, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('address1', models.CharField(max_length=200, null=True, blank=True)),
                ('address2', models.CharField(max_length=200, null=True, blank=True)),
                ('address3', models.CharField(max_length=200, null=True, blank=True)),
                ('address4', models.CharField(max_length=200, null=True, blank=True)),
                ('postcode', models.CharField(max_length=9, null=True, blank=True)),
                ('location', django.contrib.gis.db.models.fields.PointField(srid=4326, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Prescription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('presentation_code', models.CharField(db_index=True, max_length=15, validators=[django.core.validators.RegexValidator(b'^[\\w]*$', message=b'name must be alphanumeric', code=b'Invalid name')])),
                ('presentation_name', models.CharField(max_length=1000)),
                ('total_items', models.IntegerField()),
                ('net_cost', models.FloatField()),
                ('actual_cost', models.FloatField()),
                ('quantity', models.FloatField()),
                ('processing_date', models.DateField(db_index=True)),
                ('price_per_unit', models.FloatField()),
                ('chemical', models.ForeignKey(to='frontend.Chemical')),
                ('pct', models.ForeignKey(to='frontend.PCT')),
                ('practice', models.ForeignKey(to='frontend.Practice')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Section',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('chapter', models.ForeignKey(to='frontend.Chapter')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SHA',
            fields=[
                ('code', models.CharField(help_text=b'Strategic health authority code', max_length=3, serialize=False, primary_key=True)),
                ('ons_code', models.CharField(max_length=9, null=True, blank=True)),
                ('name', models.CharField(max_length=200, null=True, blank=True)),
                ('boundary', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='prescription',
            name='sha',
            field=models.ForeignKey(to='frontend.SHA'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='paragraph',
            name='section',
            field=models.ForeignKey(to='frontend.Section'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='chemical',
            unique_together=set([('bnf_code', 'chem_name')]),
        ),
    ]
