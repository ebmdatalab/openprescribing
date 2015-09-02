# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0025_practiceprescribingsetting'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='practiceprescribingsetting',
            unique_together=set([('practice', 'date', 'setting')]),
        ),
    ]
