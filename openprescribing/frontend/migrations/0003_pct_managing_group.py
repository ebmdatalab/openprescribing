# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0002_auto_20150320_1615'),
    ]

    operations = [
        migrations.AddField(
            model_name='pct',
            name='managing_group',
            field=models.ForeignKey(blank=True, to='frontend.SHA', null=True),
            preserve_default=True,
        ),
    ]
