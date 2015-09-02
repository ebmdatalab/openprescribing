# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0027_auto_20150706_1039'),
    ]

    operations = [
        migrations.CreateModel(
            name='PracticeIsDispensing',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('practice', models.ForeignKey(to='frontend.Practice')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='practiceisdispensing',
            unique_together=set([('practice', 'date')]),
        ),
    ]
