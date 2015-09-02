# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0012_auto_20150502_0648'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='section',
            options={},
        ),
        migrations.RemoveField(
            model_name='section',
            name='bnf_chapter',
        ),
        migrations.RemoveField(
            model_name='section',
            name='bnf_para',
        ),
        migrations.RemoveField(
            model_name='section',
            name='bnf_section',
        ),
        migrations.RemoveField(
            model_name='section',
            name='bnf_subpara',
        ),
    ]
