# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0029_remove_practice_is_dispensing'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('bnf_code', models.CharField(max_length=9, serialize=False, primary_key=True, validators=[django.core.validators.RegexValidator(b'^[\\w]*$', message=b'name must be alphanumeric', code=b'Invalid name')])),
                ('name', models.CharField(max_length=200)),
                ('is_generic', models.BooleanField()),
            ],
        ),
    ]
