import json
import logging
import os
import re
import requests
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from config import REGISTRY
from utils import configure_logging, get_secret, get_homeassistant_state

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
        self.max_version_query_pages = app_json['max_version_query_pages'] if 'max_version_query_pages' in app_json else None
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
            self.latest_version=self.get_latest_local_image_tag()
        elif self.docker_url:
            try:
                self.latest_version=self.get_latest_dockerhub_release_version(self.docker_url)
            except:
                self.latest_version="Unknown"
        else:
            try:
                self.latest_version=self.get_latest_github_release_version(self.git_hub_url,self.github_version_field, self.version_pattern)
                if self.name == "photoprism":
                    self.latest_version=self.latest_version.split('-')[0]
            except Exception as e:
                logging.error("Failed getting latest version for " + self.name, e)

    def get_latest_local_image_tag(self):
        pattern = re.compile(self.version_pattern)
        image_name=self.image.split("/")[1]
        url = f"https://{REGISTRY}/v2/{image_name}/tags/list"
        try:
            resp = requests.get(url, verify=False)
            resp.raise_for_status()
            tags = resp.json().get("tags", [])
            if tags:
                tags=[ s for s in tags if pattern.match(s) ]
                tags.sort()
                return tags[-1]
            else:
                return "NOT_SET"
        except:
            logger.error(f"No tags found for image '{image_name}'")
            return "NOT_SET"

    def get_latest_dockerhub_release_version(self, url=None):
        pattern = re.compile(self.version_pattern)
        all_images=[]
        curl_count=0
        while url != None and curl_count < int(self.max_version_query_pages):
            curl_count = curl_count+1
            resp = requests.get(url)
            data = resp.json()
            images=data['results']
            images = [e['name'] for e in images]
            all_images.extend([ s for s in images if pattern.match(s) ])
            url = data['next']
        all_images.sort()
        return all_images[-1]

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
        latest_version = "not found"
        try:
            pattern = re.compile(version_pattern)
            for version in data:
                version_tag=version[github_version_field]
                if pattern.match(version_tag):
                    latest_version = version_tag
                    break;
        except Exception as e:
            logging.error(data, e)
        return latest_version

