# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2017-10-04 12:30
from __future__ import unicode_literals
import json
import os

from django.db import migrations, models

def _get_measure_data(measure_id):
    fpath = os.path.dirname(__file__)
    fname = os.path.join(
        fpath,
        ("../management/commands/measure_definitions/"
         "%s.json") % measure_id)
    return json.load(open(fname, 'r'))

def arrays_to_strings(measure_json):
    """To facilitate readability via newlines, we express some JSON
    strings as arrays, but store them as strings.

    Returns the json with such fields converted to strings.

    """
    converted = {}
    fields_to_convert = [
        'title', 'description', 'why_it_matters', 'numerator_columns',
        'numerator_where', 'denominator_columns', 'denominator_where']
    for k, v in measure_json.items():
        if k in fields_to_convert and isinstance(v, list):
            converted[k] = ' '.join(v)
        else:
            converted[k] = v

    return converted


def set_measure_fields(apps, schema_editor):
    Measure = apps.get_model('frontend', 'Measure')
    for m in Measure.objects.all().iterator():
        v = arrays_to_strings(_get_measure_data(m.id))
        m.numerator_from = v['numerator_from']
        m.numerator_where = v['numerator_where']
        m.numerator_columns = v['numerator_columns']
        m.denominator_from = v['denominator_from']
        m.denominator_where = v['denominator_where']
        m.denominator_columns = v['denominator_columns']
        m.save()

class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0030_measure_tags_focus'),
    ]

    operations = [
        migrations.AddField(
            model_name='measure',
            name='denominator_columns',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='measure',
            name='denominator_from',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='measure',
            name='denominator_where',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='measure',
            name='numerator_columns',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='measure',
            name='numerator_from',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='measure',
            name='numerator_where',
            field=models.TextField(null=True),
        ),

        migrations.RunPython(set_measure_fields),

        migrations.AlterField(
            model_name='measure',
            name='denominator_columns',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='measure',
            name='denominator_from',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='measure',
            name='denominator_where',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='measure',
            name='numerator_columns',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='measure',
            name='numerator_from',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='measure',
            name='numerator_where',
            field=models.TextField(),
        ),
    ]
