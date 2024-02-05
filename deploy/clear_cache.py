import json
import os

import dotenv
import requests

# This zone ID may change if/when our account changes
# Run `list_cloudflare_zones` (below) to get a full list
ZONE_ID = "198bb61a3679d0e1545e838a8f0c25b9"


def list_cloudflare_zones():
    url = "https://api.cloudflare.com/client/v4/zones"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ['CF_API_KEY']}",
    }
    result = json.loads(requests.get(url, headers=headers).text)
    zones = [{"name": x["name"], "id": x["id"]} for x in result["result"]]
    print(zones)


def clear_cloudflare():
    url = "https://api.cloudflare.com/client/v4/zones/%s"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ['CF_API_KEY']}",
    }
    data = {"purge_everything": True}
    result = json.loads(
        requests.delete(
            url % ZONE_ID + "/purge_cache", headers=headers, data=json.dumps(data)
        ).text
    )
    if result["success"]:
        print("Cloudflare clearing succeeded")
    else:
        raise ValueError(
            "Cloudflare clearing failed: %s" % json.dumps(result, indent=2)
        )


if __name__ == "__main__":
    env_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "..", "environment"
    )

    dotenv.read_dotenv(env_path, override=True)
    clear_cloudflare()
