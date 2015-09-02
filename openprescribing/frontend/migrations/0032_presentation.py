# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0031_auto_20150727_1152'),
    ]

    operations = [
        migrations.CreateModel(
            name='Presentation',
            fields=[
                ('bnf_code', models.CharField(max_length=15, serialize=False, primary_key=True, validators=[django.core.validators.RegexValidator(b'^[\\w]*$', message=b'name must be alphanumeric', code=b'Invalid name')])),
                ('name', models.CharField(max_length=200)),
                ('is_generic', models.BooleanField()),
            ],
        ),
    ]
