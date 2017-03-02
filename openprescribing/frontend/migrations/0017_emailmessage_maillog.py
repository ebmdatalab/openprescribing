# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2017-03-02 15:38
from __future__ import unicode_literals

from django.conf import settings
import django.contrib.postgres.fields
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [(b'frontend', '0017_emailmessage_maillog_squashed_0021_auto_20170301_1627'), (b'frontend', '0018_auto_20170302_1533')]

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('frontend', '0016_remove_prescription_chemical'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailMessage',
            fields=[
                ('message_id', models.CharField(max_length=998, primary_key=True, serialize=False)),
                ('pickled_message', models.BinaryField()),
                ('subject', models.CharField(max_length=200)),
                ('tags', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(db_index=True, max_length=100), null=True, size=None)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('send_count', models.SmallIntegerField(default=0)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('to', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(db_index=True, max_length=254), size=None)),
            ],
        ),
        migrations.CreateModel(
            name='MailLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('metadata', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('recipient', models.CharField(db_index=True, max_length=254)),
                ('tags', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(db_index=True, max_length=100), null=True, size=None)),
                ('reject_reason', models.CharField(blank=True, max_length=15, null=True)),
                ('message_id', models.CharField(db_index=True, max_length=998)),
                ('event_type', models.CharField(choices=[(b'complained', b'complained'), (b'delivered', b'delivered'), (b'inbound_failed', b'inbound_failed'), (b'clicked', b'clicked'), (b'opened', b'opened'), (b'subscribed', b'subscribed'), (b'deferred', b'deferred'), (b'inbound', b'inbound'), (b'unknown', b'unknown'), (b'rejected', b'rejected'), (b'queued', b'queued'), (b'failed', b'failed'), (b'autoresponded', b'autoresponded'), (b'unsubscribed', b'unsubscribed'), (b'bounced', b'bounced'), (b'sent', b'sent')], db_index=True, max_length=15)),
                ('timestamp', models.DateTimeField(blank=True, null=True)),
            ],
        ),
    ]
