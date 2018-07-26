import os

import requests

from django.conf import settings


def notify_slack(message):
    """Posts the message to #general

    See https://my.slack.com/services/new/incoming-webhook/
    """
    if not settings.SLACK_SENDING_ACTIVE:
        return

    webhook_url = settings.SLACK_GENERAL_POST_KEY
    slack_data = {'text': message}

    response = requests.post(webhook_url, json=slack_data)
    if response.status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
        )
