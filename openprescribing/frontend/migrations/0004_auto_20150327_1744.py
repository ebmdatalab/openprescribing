# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0003_pct_managing_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pct',
            name='boundary',
            field=django.contrib.gis.db.models.fields.GeometryField(srid=4326, null=True, blank=True),
            preserve_default=True,
        ),
    ]
