# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0013_auto_20150502_0708'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='section',
            options={'ordering': ['bnf_chapter', 'bnf_section', 'bnf_para']},
        ),
        migrations.AddField(
            model_name='section',
            name='bnf_chapter',
            field=models.IntegerField(default=1, max_length=2),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='section',
            name='bnf_para',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='section',
            name='bnf_section',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
