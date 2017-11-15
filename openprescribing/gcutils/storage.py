from google.cloud import storage as gcs

from django.conf import settings


class Client(object):
    '''A dumb proxy for gcs.Client'''

    def __init__(self):
        self.gcs_client = gcs.Client(project=settings.BQ_PROJECT)

    def __getattr__(self, name):
        return getattr(self.gcs_client, name)
