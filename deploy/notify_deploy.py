import os
import sys

import dotenv
import requests


def notify_slack(message):
    """Posts the message to #general"""
    # Set the webhook_url to the one provided by Slack when you create
    # the webhook at
    # https://my.slack.com/services/new/incoming-webhook/
    webhook_url = os.environ["SLACK_TECHNOISE_POST_KEY"]
    slack_data = {"text": message}

    response = requests.post(webhook_url, json=slack_data)
    if response.status_code != 200:
        raise ValueError(
            "Request to slack returned an error %s, the response is:\n%s"
            % (response.status_code, response.text)
        )


if __name__ == "__main__":
    env_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "..", "environment"
    )
    dotenv.read_dotenv(env_path, override=True)

    _, revision, url, fab_env = sys.argv
    notify_slack("A #deploy just finished. Changes here: {}".format(url))
