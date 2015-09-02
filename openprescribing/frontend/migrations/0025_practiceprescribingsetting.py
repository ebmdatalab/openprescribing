# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0024_practicelist_pct'),
    ]

    operations = [
        migrations.CreateModel(
            name='PracticePrescribingSetting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('setting', models.IntegerField(default=-1, choices=[(-1, b'Unknown'), (0, b'Other'), (1, b'WIC Practice'), (2, b'OOH Practice'), (3, b'WIC + OOH Practice'), (4, b'GP Practice'), (8, b'Public Health Service'), (9, b'Community Health Service'), (10, b'Hospital Service'), (11, b'Optometry Service'), (12, b'Urgent & Emergency Care'), (13, b'Hospice'), (14, b'Care Home / Nursing Home'), (15, b'Border Force'), (16, b'Young Offender Institution'), (17, b'Secure Training Centre'), (18, b"Secure Children's Home"), (19, b'Immigration Removal Centre'), (20, b'Court'), (21, b'Police Custody'), (22, b'Sexual Assault Referral Centre (SARC)'), (24, b'Other - Justice Estate'), (25, b'Prison')])),
                ('practice', models.ForeignKey(to='frontend.Practice')),
            ],
        ),
    ]
