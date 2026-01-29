import logging
import json
import os
import requests
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from utils import configure_logging, get_secret

logger = logging.getLogger(__name__)
configure_logging()

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

