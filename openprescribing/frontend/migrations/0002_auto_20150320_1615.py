# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='paragraph',
            name='section',
        ),
        migrations.RemoveField(
            model_name='section',
            name='chapter',
        ),
        migrations.AlterField(
            model_name='chapter',
            name='id',
            field=models.CharField(max_length=2, serialize=False, primary_key=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='paragraph',
            name='id',
            field=models.CharField(max_length=6, serialize=False, primary_key=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='section',
            name='id',
            field=models.CharField(max_length=4, serialize=False, primary_key=True),
            preserve_default=True,
        ),
    ]
