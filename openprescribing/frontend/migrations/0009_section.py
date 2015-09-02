# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0008_auto_20150429_2137'),
    ]

    operations = [
        migrations.CreateModel(
            name='Section',
            fields=[
                ('bnf_id', models.CharField(max_length=8, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('number_str', models.CharField(default=b'1.1.1', max_length=12)),
                ('bnf_chapter', models.IntegerField()),
                ('bnf_section', models.IntegerField(null=True, blank=True)),
                ('bnf_para', models.IntegerField(null=True, blank=True)),
                ('bnf_subpara', models.IntegerField(null=True, blank=True)),
            ],
            options={
                'ordering': ['bnf_chapter', 'bnf_section', 'bnf_para', 'bnf_subpara'],
            },
            bases=(models.Model,),
        ),
    ]
