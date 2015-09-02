# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0022_auto_20150529_1627'),
    ]

    operations = [
        migrations.RenameField(
            model_name='practicelist',
            old_name='astro_pu_cost_2013',
            new_name='astro_pu_cost',
        ),
    ]
