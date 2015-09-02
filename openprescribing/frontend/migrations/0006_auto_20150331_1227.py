# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0005_auto_20150331_1217'),
    ]

    operations = [
        migrations.AlterField(
            model_name='qofprevalence',
            name='indicator_group',
            field=models.CharField(max_length=10),
            preserve_default=True,
        ),
    ]
