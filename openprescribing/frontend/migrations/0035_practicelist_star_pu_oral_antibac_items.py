# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0034_practicelist_astro_pu_items'),
    ]

    operations = [
        migrations.AddField(
            model_name='practicelist',
            name='star_pu_oral_antibac_items',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
    ]
