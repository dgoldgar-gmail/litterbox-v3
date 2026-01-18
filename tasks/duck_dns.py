import logging
import json
import os
import requests
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)

from utils import get_secret

def update_dns_info():
    token=get_secret("habitrail_token")
    domains=["authabitrail","habitrail"]
    for domain in domains:
        logger.info(f"Refreshing {domain}")
        url = "https://www.duckdns.org/update"
        params = {
            "domains": domain,
            "token": token,
            "verbose": "true",
        }

        logger.info("Updating DuckDNS for domain=%s", domain)
        response = requests.get(url, params=params, timeout=10)

        logger.info("DuckDNS response: %s", response.text)

