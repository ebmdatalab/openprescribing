# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0010_auto_20150502_0645'),
    ]

    operations = [
        migrations.AlterField(
            model_name='section',
            name='bnf_subpara',
            field=models.CharField(max_length=8, null=True, blank=True),
            preserve_default=True,
        ),
    ]
