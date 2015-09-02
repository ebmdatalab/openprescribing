# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0018_auto_20150528_1641'),
    ]

    operations = [
        migrations.RenameField(
            model_name='practicelist',
            old_name='in_quarter_starting',
            new_name='quarter_start_date',
        ),
        migrations.RemoveField(
            model_name='pct',
            name='list_size_13',
        ),
    ]
