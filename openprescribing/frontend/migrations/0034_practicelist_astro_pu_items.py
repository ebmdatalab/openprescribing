# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0033_auto_20150727_1219'),
    ]

    operations = [
        migrations.AddField(
            model_name='practicelist',
            name='astro_pu_items',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
    ]
