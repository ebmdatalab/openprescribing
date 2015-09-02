# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0032_presentation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='presentation',
            name='is_generic',
            field=models.NullBooleanField(default=None),
        ),
    ]
