from __future__ import unicode_literals

from django.utils import timezone
from django.db import models


class TaskLog(models.Model):
    run_id = models.CharField(max_length=100)
    task_name = models.CharField(max_length=100)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True)
    status = models.CharField(max_length=100, null=True)

    def mark_succeeded(self):
        self.mark_complete('successful')

    def mark_failed(self):
        self.mark_complete('failed')

    def mark_complete(self, status):
        assert self.status is None
        assert self.ended_at is None
        self.status = status
        self.ended_at = timezone.now()
        self.save()
