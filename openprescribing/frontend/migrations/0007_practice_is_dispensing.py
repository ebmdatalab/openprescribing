# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0006_auto_20150331_1227'),
    ]

    operations = [
        migrations.AddField(
            model_name='practice',
            name='is_dispensing',
            field=models.NullBooleanField(default=None),
            preserve_default=False,
        ),
    ]
