# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0007_practice_is_dispensing'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Chapter',
        ),
        migrations.DeleteModel(
            name='Paragraph',
        ),
        migrations.DeleteModel(
            name='Section',
        ),
    ]
