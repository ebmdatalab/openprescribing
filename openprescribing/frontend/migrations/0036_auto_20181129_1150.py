# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-11-29 11:50


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0035_auto_20180918_1126_squashed_0037_auto_20180919_0938'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegionalTeam',
            fields=[
                ('code', models.CharField(max_length=3, primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, max_length=200, null=True)),
                ('open_date', models.DateField(blank=True, null=True)),
                ('close_date', models.DateField(blank=True, null=True)),
                ('address', models.CharField(blank=True, max_length=400, null=True)),
                ('postcode', models.CharField(blank=True, max_length=10, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='STP',
            fields=[
                ('ons_code', models.CharField(max_length=9, primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, max_length=200, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='pct',
            name='regional_team',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='frontend.RegionalTeam'),
        ),
        migrations.AddField(
            model_name='pct',
            name='stp',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='frontend.STP'),
        ),
    ]
