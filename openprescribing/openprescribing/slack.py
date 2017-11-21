import os

import requests

from django.conf import settings


def notify_slack(message):
    """Posts the message to #general
    """
    # Set the webhook_url to the one provided by Slack when you create
    # the webhook at
    # https://my.slack.com/services/new/incoming-webhook/
    webhook_url = settings.SLACK_GENERAL_POST_KEY
    if not webhook_url:
        return

    slack_data = {'text': message}

    response = requests.post(webhook_url, json=slack_data)
    if response.status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
        )
