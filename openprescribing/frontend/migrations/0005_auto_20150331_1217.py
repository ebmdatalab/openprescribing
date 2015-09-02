# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0004_auto_20150327_1744'),
    ]

    operations = [
        migrations.CreateModel(
            name='QOFPrevalence',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_year', models.IntegerField()),
                ('indicator_group', models.CharField(max_length=3)),
                ('register_description', models.CharField(max_length=100)),
                ('disease_register_size', models.IntegerField()),
                ('pct', models.ForeignKey(blank=True, to='frontend.PCT', null=True)),
                ('practice', models.ForeignKey(blank=True, to='frontend.Practice', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='pct',
            name='list_size_13',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='practice',
            name='list_size_13',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
