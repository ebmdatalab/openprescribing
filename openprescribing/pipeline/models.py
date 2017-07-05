from __future__ import unicode_literals

from django.utils import timezone
from django.db import models


class TaskLog(models.Model):
    run_id = models.CharField(max_length=100)
    task_name = models.CharField(max_length=100)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True)
    status = models.CharField(max_length=100, null=True)
    formatted_tb = models.TextField(null=True)

    SUCCESSFUL = 'successful'
    FAILED = 'failed'

    def mark_succeeded(self):
        assert self.status is None
        assert self.ended_at is None
        self.status = self.SUCCESSFUL
        self.ended_at = timezone.now()
        self.save()

    def mark_failed(self, formatted_tb):
        assert self.status is None
        assert self.ended_at is None
        self.status = self.FAILED
        self.ended_at = timezone.now()
        self.formatted_tb = formatted_tb
        self.save()
