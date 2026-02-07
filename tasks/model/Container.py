import docker
import json
import logging
import os
import subprocess
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from config import Configuration
from docker_daemon_client import DockerDaemonClient
from home_assistant_client import HomeAssistantClient
from utils import configure_logging, get_timestamp


configuration = Configuration()
docker_daemon_client = DockerDaemonClient()
home_assistant_client = HomeAssistantClient()

logger = logging.getLogger(__name__)
configure_logging()

class Container:
    def __init__(self, host, app):
        self.host = host
        self.app = app
        self.current_version = None
        self.container_created_at =  None
        self.container_state = None
        self.container_status = None
        self.container_image = None
        self.latest_version = None
        logger.debug(f"Initializing container: {app} on {host}")

    def get_json(self):
        output = {}
        output['host'] = self.host
        output['app'] = self.app
        output['current_version'] = self.current_version
        output['container_created_at'] = self.container_created_at
        output['container_state'] = self.container_state
        output['container_status'] = self.container_status
        output['container_image'] = self.container_image
        return output

    def collect_version_info(self):
        logger.debug(f"Collecting current version info for container: {self.app} on {self.host}")
        self.latest_version = home_assistant_client.get_homeassistant_state(f"sensor.{self.app}_latest_version")["state"]
        logger.info(f"Found latest_version for {self.app} in state... {self.latest_version}")
        self.collection_timestamp = get_timestamp()
        try:
            if self.app == "tasmota":
                self.current_version = None
                #return get_tasmota_device_versions_map();
            elif self.app == "webssh":
                self.current_version = self.get_webssh_current_version();
            else:
                self.current_version = self.get_current_version_by_docker_tag()
        except Exception as e:
            logging.error(f"Error collecting current_version_info for {self.app} on {self.host}", e)
            self.current_version = None

    def get_current_version_by_docker_tag(self):
        try:
            logger.debug("-------> Use docker client...")
            client = docker.from_env()
          
            containers = client.containers.list(filters={"name": self.app})
            if not containers:
                logger.warning(f"No running container found for {self.app} locally")
                return configuration.UNKNOWN

            image_full_name = containers[0].image.tags[0]
            _, _, tag = image_full_name.rpartition(":")
            logger.debug(f"Got tag for {self.app}  container: {tag}")
            return tag
        except Exception as e:
            logger.warning(f"Local Docker SDK call failed: {e}")
            return configuration.UNKNOWN

    def get_frigate_current_version(host):
        sensor_value=get_state("update.frigate_server")
        return sensor_value['attributes']['installed_version']

    def get_webssh_current_version(self):
        try:
            client = docker.from_env()
            container = client.containers.get("webssh")
            exit_code, output = container.exec_run(
                cmd="/usr/local/bin/python /code/run.py --version",
                stdout=True,
                stderr=True
            )
            if exit_code == 0:
                version = output.decode("utf-8").strip()
                logger.debug(f"Webssh current version: {version}")
                return f"v{version}"
            else:
                logger.error(f"Version command failed with exit code {exit_code}")
                return configuration.UNKNOWN
        except docker.errors.NotFound:
            logger.error("Container 'webssh' not found.")
            return configuration.UNKNOWN
        except Exception as e:
            logger.error(f"Failed to get webssh version via SDK: {e}")
            return configuration.UNKNOWN



    def collect_docker_stats(self):
        logger.debug(f"Collecting local docker stats for {self.app}")
        try:
            attrs = docker_daemon_client.get_container_attrs(self.app)
            self.container_created_at = attrs.get('Created', 'Unknown')
            self.container_state = attrs.get('State', {}).get('Status', 'Unknown')
            self.container_status = attrs.get('State', {}).get('Health', {}).get('Status', self.container_state)
            self.container_image = attrs.get('Config', {}).get('Image', 'Unknown')
        except (docker.errors.NotFound, Exception) as e:
            logger.info(f"Docker reports no container info for {self.app}: {e}")
            self.container_created_at = "Container Down"
            self.container_state = "Container Down"
            self.container_status = "Container Down"
            self.container_image = "Container Down"

    def send_single_state(self, attribute, data, sensor_attributes=None):
        logger.debug(f"send_single_state: {self.host} {self.app} {attribute} {data}" )
        short_host = self.host.split("-")[1]
        sensor_name = f'sensor.{short_host}_{self.app}_{attribute}'
        payload = {}
        payload['state'] = data
        if sensor_attributes is None:
            sensor_attributes = {}

        sensor_attributes['collection_timestamp'] = self.collection_timestamp
        payload['attributes'] = sensor_attributes
        home_assistant_client.set_homeassistant_state(sensor_name, payload)

    def send_state_data(self):
        logger.debug(f"Sending state data for {self.app} on {self.host}")
        self.send_single_state("current_version", self.current_version)
        self.send_single_state("collection_timestamp", self.collection_timestamp, { "icon": "mdi:timer" } )
        self.send_single_state("created_at", self.container_created_at, { "icon": "mdi:baby-carriage" })
        icon = "mdi:run" if self.container_state == "running" else "mdi:sleep"
        self.send_single_state("state", self.container_state, { "icon": icon } )
        self.send_single_state("status", self.container_status, { "icon": "mdi:calendar-clock" } )
        self.send_single_state("image", self.container_image, { "icon": "mdi:image" } )

        version_info = self.current_version if self.current_version == self.latest_version else f"( ↑ {self.latest_version} ↑ ) {self.current_version}"
        version_info = version_info if self.current_version != configuration.UNKNOWN else configuration.UNKNOWN

        icon = "mdi:check" if self.current_version == self.latest_version else "mdi:package-up"
        icon = icon if self.current_version != configuration.UNKNOWN else "mdi:alert-box-outline"

        self.notify()

        self.send_single_state("version_info", version_info, { "icon": icon } )

    def notify(self):
        unknown_version_id = f"Unknown version for {self.app} on {self.host}"
        update_version_id = f"Update available for {self.app} on {self.host}"

        if self.current_version == configuration.UNKNOWN:
            home_assistant_client.send_homeassistant_notification(
                service="persistent_notification",
                message=unknown_version_id,
                title=unknown_version_id
            )
        elif self.current_version != self.latest_version:
            home_assistant_client.send_homeassistant_notification(
                service="persistent_notification",
                message=f"New version {self.latest_version} is available for {self.app} on {self.host}.  Current version is {self.current_version}.",
                title=update_version_id
            )
        else:
            home_assistant_client.dismiss_homeassistant_notification(id=unknown_version_id)
            home_assistant_client.dismiss_homeassistant_notification(id=update_version_id)
