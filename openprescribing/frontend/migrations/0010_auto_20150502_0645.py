# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0009_section'),
    ]

    operations = [
        migrations.AlterField(
            model_name='section',
            name='bnf_chapter',
            field=models.CharField(max_length=2),
        ),
        migrations.AlterField(
            model_name='section',
            name='bnf_para',
            field=models.CharField(max_length=6, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='section',
            name='bnf_section',
            field=models.CharField(max_length=4, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='section',
            name='bnf_subpara',
            field=models.IntegerField(max_length=8, null=True, blank=True),
        ),
    ]
