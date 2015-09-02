# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0023_auto_20150529_1630'),
    ]

    operations = [
        migrations.AddField(
            model_name='practicelist',
            name='pct',
            field=models.ForeignKey(blank=True, to='frontend.PCT', null=True),
        ),
    ]
