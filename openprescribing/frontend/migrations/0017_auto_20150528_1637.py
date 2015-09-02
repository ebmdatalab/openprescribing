# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0016_auto_20150518_1055'),
    ]

    operations = [
        migrations.CreateModel(
            name='PracticeList',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('in_quarter_starting', models.DateField()),
                ('male_0_4', models.IntegerField()),
                ('female_0_4', models.IntegerField()),
                ('male_5_14', models.IntegerField()),
                ('female_5_14', models.IntegerField()),
                ('male_15_24', models.IntegerField()),
                ('female_15_24', models.IntegerField()),
                ('male_25_34', models.IntegerField()),
                ('female_25_34', models.IntegerField()),
                ('male_35_44', models.IntegerField()),
                ('female_35_44', models.IntegerField()),
                ('male_45_54', models.IntegerField()),
                ('female_45_54', models.IntegerField()),
                ('male_55_64', models.IntegerField()),
                ('female_55_64', models.IntegerField()),
                ('male_65_74', models.IntegerField()),
                ('female_65_74', models.IntegerField()),
                ('male_75_plus', models.IntegerField()),
                ('female_75_plus', models.IntegerField()),
                ('total_list_size', models.IntegerField()),
                ('astro_pu_cost_2013', models.FloatField()),
            ],
        ),
        migrations.RemoveField(
            model_name='practice',
            name='list_size_13',
        ),
        migrations.AddField(
            model_name='practicelist',
            name='practice',
            field=models.ForeignKey(to='frontend.Practice'),
        ),
    ]
