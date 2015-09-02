# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0019_auto_20150529_0944'),
    ]

    operations = [
        migrations.AddField(
            model_name='practicelist',
            name='quarter_end_date',
            field=models.DateField(default=datetime.datetime(2015, 5, 29, 14, 21, 48, 335172, tzinfo=utc)),
            preserve_default=False,
        ),
    ]
