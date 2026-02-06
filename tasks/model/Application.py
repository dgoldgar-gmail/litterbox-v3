import json
import logging
import os
import re
import requests
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from config import REGISTRY, UNKNOWN
from utils import configure_logging, get_secret, get_homeassistant_state, get_latest_dockerhub_release_version, get_latest_local_registry_image_version

logger = logging.getLogger(__name__)
configure_logging()

class Application:
    def __init__(self, app_json):
        logger.debug(f"Initializing app {app_json['name']}")
        self.json = app_json
        self.name = app_json['name']
        self.live = app_json['live']
        self.managed = app_json['managed']
        self.notify_version = app_json['notify_version']
        self.platform = app_json['platform']
        self.version_pattern = app_json['version_pattern'] if 'version_pattern' in app_json else None
        self.github_version_field = app_json['github_version_field'] if 'github_version_field' in app_json else None
        self.docker_url = app_json['docker_url'] if 'docker_url' in app_json else None
        self.git_hub_url = app_json['git_hub_url'] if 'git_hub_url' in app_json else None
        self.docker = app_json['docker']
        self.image = self.docker['image'] if self.docker != None else None

    def get_json(self):
        output = {}
        output['name'] = self.name
        output['latest_version'] = self.latest_version
        output['managed'] = self.managed
        output['notify_version'] = self.notify_version
        return output

    def get_latest_app_version(self):
        logger.debug(f"Getting latest app version for {self.name}")
        if self.name == "frigate":
            try:
                sensor_value=get_homeassistant_state("update.frigate_server")
                sensor_value=sensor_value['attributes']['installed_version']
                logger.debug(f"Sensor value for update.frigate_server is {sensor_value}")
                self.latest_version = sensor_value
            except Exception as e:
                logger.error(f"Failure in getting installed_version for frigate: {e}")
                self.latest_version = "NOT SET"
        elif REGISTRY in self.image:
            logger.info(f"Getting latest version for registry image {self.image}")
            self.latest_version=get_latest_local_registry_image_version(self.docker_url, self.version_pattern)
        elif self.docker_url:
            try:
                # defensive...if the api call failed, keep the old version if we have one.
                latest_version = get_latest_dockerhub_release_version(self.docker_url, self.version_pattern)
                logger.debug(f"Latest version for {self.name}  is {latest_version}")
                if latest_version == UNKNOWN and self.latest_version != UNKNOWN:
                    logger.info(f"Failed to get latest version for {self.name} using dockerhub api, keeping old version {self.latest_version}")
                else:
                    self.latest_version=latest_version
            except Exception as e:
                logger.warn(f"Caught exception, setting latest_version to {UNKNOWN} {e}")
                self.latest_version=UNKNOWN

    def get_latest_github_release_version(self, url=None,github_version_field=None,  version_pattern=None):
        logging.debug("get_latest_github_release_version for " + url)
        github_token=get_secret("github_token")
        headers = {}
        headers['Accept'] = "application/vnd.github+json"
        headers['Authorization'] = "Bearer " + str(github_token)
        headers['X-GitHub-Api-Version'] = "2022-11-28"
        resp = requests.get( url, headers=headers)
        #print(resp.headers)
        data = resp.json()
        latest_version = UNKNOWN
        try:
            pattern = re.compile(version_pattern)
            for version in data:
                version_tag=version[github_version_field]
                logging.info(f"Version tag for {self.name} is {version_tag} matching {version_pattern}")
                if pattern.match(version_tag):
                    latest_version = version_tag
                    break
        except Exception as e:
            logging.error(data, e)
        return latest_version
