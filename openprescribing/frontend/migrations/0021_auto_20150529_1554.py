# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0020_practicelist_quarter_end_date'),
    ]

    operations = [
        migrations.RenameField(
            model_name='practicelist',
            old_name='quarter_end_date',
            new_name='month_date',
        ),
        migrations.RemoveField(
            model_name='practicelist',
            name='quarter_start_date',
        ),
    ]
