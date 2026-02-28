import json
import logging
import requests

from config import Configuration
from utils import get_secret

logger = logging.getLogger(__name__)

class HomeAssistantClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HomeAssistantClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.configuration = Configuration()

    # --- Home Assistant Helper Functions ---
    def get_homeassistant_state(self, name):
        url=f"{self.configuration.HOME_ASSISTANT_API_URL}/states/{name}"
        headers = {}
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = "Bearer " + get_secret("ha_assistant")
        logger.debug(f"Get state for {name}")
        logger.debug(f"URL: {url}")
        output=requests.get(url, headers=headers, verify=False)
        return output.json()

    def set_homeassistant_state(self, name, payload):
        url=f"{self.configuration.HOME_ASSISTANT_API_URL}/states/{name}"
        headers = {}
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = "Bearer " + get_secret("ha_assistant")
        logger.debug(
            f"\n<<< {name} >>>\n%s",
            json.dumps(payload, indent=2, sort_keys=True)
        )
        r = requests.post(url , data=json.dumps(payload), headers=headers, verify=False)
        r.raise_for_status()

    def send_homeassistant_notification(self, service, message, title=None, data=None):
        url = f"{self.configuration.HOME_ASSISTANT_API_URL}/services/{service}/create"
        payload = {"message": message}
        headers = {}
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = "Bearer " + get_secret("ha_assistant")
        logger.info(
            f"\n<<< ALERT >>>\n%s",
            json.dumps(payload, indent=2, sort_keys=True)
        )
        if title:
            payload['notification_id'] = title
            payload["title"] = title
        else:
            payload['title'] = message
            payload['notification_id'] = message
        # TODO: This works for persistent, but not for cell phone i think....
        if data:
            payload["data"] = data
        r = requests.post(url, headers=headers, json=payload, timeout=5, verify=False)
        r.raise_for_status()

    def dismiss_homeassistant_notification(self, id):
        url = f"{self.configuration.HOME_ASSISTANT_API_URL}/services/persistent_notification/dismiss"
        payload = { "notification_id": id }
        headers = {}
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = "Bearer " + get_secret("ha_assistant")
        logger.debug(
            f"\n<<< DISMISS >>>\n%s",
            json.dumps(payload, indent=2, sort_keys=True)
        )
        r = requests.post(url, headers=headers, json=payload, timeout=5, verify=False)
        r.raise_for_status()