# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0014_auto_20150502_0708'),
    ]

    operations = [
        migrations.AlterField(
            model_name='section',
            name='bnf_chapter',
            field=models.IntegerField(),
            preserve_default=True,
        ),
    ]
