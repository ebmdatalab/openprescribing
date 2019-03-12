import os
import requests
import sys

import dotenv


# Newrelic Apps
NEWRELIC_APPIDS = {
    'production': '45170403',
    'staging': '45937313',
    'test': '45170011'
}


def notify_newrelic(revision, url, fab_env='production'):
    payload = {
        "deployment": {
            "revision": revision,
            "changelog": url
        }
    }
    app_id = NEWRELIC_APPIDS[fab_env]
    headers = {'X-Api-Key': os.environ['NEWRELIC_API_KEY']}
    response = requests.post(
        ("https://api.newrelic.com/v2/applications/"
         "%s/deployments.json" % app_id),
        headers=headers,
        json=payload)
    response.raise_for_status()


def notify_slack(message):
    """Posts the message to #general
    """
    # Set the webhook_url to the one provided by Slack when you create
    # the webhook at
    # https://my.slack.com/services/new/incoming-webhook/
    webhook_url = os.environ['SLACK_GENERAL_POST_KEY']
    slack_data = {'text': message}

    response = requests.post(webhook_url, json=slack_data)
    if response.status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
        )


if __name__ == '__main__':
    env_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        '..', 'environment'
    )
    dotenv.read_dotenv(env_path, override=True)

    _, revision, url, fab_env = sys.argv
    notify_newrelic(revision, url, fab_env=fab_env)
    notify_slack("A #deploy just finished. Changes here: {}".format(url))
