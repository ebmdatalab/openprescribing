import requests
from django.conf import settings


def notify_slack(message, is_error=False):
    """Posts the message to #technoise

    See https://my.slack.com/services/new/incoming-webhook/
    """
    if not settings.SLACK_SENDING_ACTIVE:
        return

    webhook_url = settings.SLACK_TECHNOISE_POST_KEY
    team_webhook_url = settings.SLACK_TEAM_POST_KEY
    slack_data = {"text": message}

    response = requests.post(webhook_url, json=slack_data)
    if is_error:
        # Also post error messages to relevant team channel
        response = requests.post(team_webhook_url, json=slack_data)

    if response.status_code != 200:
        raise ValueError(
            "Request to slack returned an error %s, the response is:\n%s"
            % (response.status_code, response.text)
        )
