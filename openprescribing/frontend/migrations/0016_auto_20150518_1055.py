# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0015_auto_20150502_0728'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='section',
            options={'ordering': ['bnf_id']},
        ),
    ]
