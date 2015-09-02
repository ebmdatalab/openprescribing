# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0028_auto_20150706_1409'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='practice',
            name='is_dispensing',
        ),
    ]
