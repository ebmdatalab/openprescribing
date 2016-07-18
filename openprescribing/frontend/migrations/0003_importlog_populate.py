# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from frontend.models import ImportLog
import datetime

def seed_log(apps, schema_editor):
    end = ImportLog.objects.latest_in_category('prescribing').current_at
    for year in range(2010, end.year + 1):
        for month in range(1, 13):
            if year == 2010 and month < 8 \
               or year == end.year and month > end.month:
                continue
            date = datetime.datetime(year, month, 1)
            ImportLog.objects.get_or_create(
                category='prescribing',
                filename='dummy-initial-value',
                current_at=date
            )


class Migration(migrations.Migration):
    dependencies = [
        ('frontend', '0002_importlog'),
    ]

    operations = [
        migrations.RunPython(seed_log),
    ]
