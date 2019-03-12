import json
import os
import requests

import dotenv


# This zone ID may change if/when our account changes
# Run `list_cloudflare_zones` (below) to get a full list
ZONE_ID = "198bb61a3679d0e1545e838a8f0c25b9"


def list_cloudflare_zones():
    url = 'https://api.cloudflare.com/client/v4/zones'
    headers = {
        "Content-Type": "application/json",
        "X-Auth-Key": os.environ['CF_API_KEY'],
        "X-Auth-Email": os.environ['CF_API_EMAIL']
    }
    result = json.loads(
        requests.get(url, headers=headers,).text)
    zones = map(lambda x: {'name': x['name'], 'id': x['id']},
                [x for x in result["result"]])
    print(zones)


def clear_cloudflare():
    url = 'https://api.cloudflare.com/client/v4/zones/%s'
    headers = {
        "Content-Type": "application/json",
        "X-Auth-Key": os.environ['CF_API_KEY'],
        "X-Auth-Email": os.environ['CF_API_EMAIL']
    }
    data = {'purge_everything': True}
    result = json.loads(
        requests.delete(url % ZONE_ID + '/purge_cache',
                        headers=headers, data=json.dumps(data)).text)
    if result['success']:
        print("Cloudflare clearing succeeded")
    else:
        raise ValueError("Cloudflare clearing failed: %s" %
                         json.dumps(result, indent=2))


if __name__ == '__main__':
    env_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        '..', 'environment'
    )

    dotenv.read_dotenv(env_path, override=True)
    clear_cloudflare()
