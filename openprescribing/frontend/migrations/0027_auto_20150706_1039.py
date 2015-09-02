# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0026_auto_20150706_1026'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='practiceprescribingsetting',
            unique_together=set([('practice', 'date')]),
        ),
    ]
