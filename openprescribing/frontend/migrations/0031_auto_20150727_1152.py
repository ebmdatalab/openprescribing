# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0030_product'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='bnf_code',
            field=models.CharField(max_length=11, serialize=False, primary_key=True, validators=[django.core.validators.RegexValidator(b'^[\\w]*$', message=b'name must be alphanumeric', code=b'Invalid name')]),
        ),
    ]
