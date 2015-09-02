# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0021_auto_20150529_1554'),
    ]

    operations = [
        migrations.RenameField(
            model_name='practicelist',
            old_name='month_date',
            new_name='date',
        ),
    ]
