# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0011_auto_20150502_0645'),
    ]

    operations = [
        migrations.AlterField(
            model_name='section',
            name='number_str',
            field=models.CharField(max_length=12),
            preserve_default=True,
        ),
    ]
