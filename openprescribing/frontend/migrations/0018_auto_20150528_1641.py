# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0017_auto_20150528_1637'),
    ]

    operations = [
        migrations.AddField(
            model_name='practice',
            name='area_team',
            field=models.ForeignKey(blank=True, to='frontend.SHA', null=True),
        ),
        migrations.AddField(
            model_name='practice',
            name='ccg',
            field=models.ForeignKey(blank=True, to='frontend.PCT', null=True),
        ),
    ]
