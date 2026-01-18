import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))


import logging
logger = logging.getLogger(__name__)

#paramiko_level = logging.DEBUG if debug else logging.WARNING
paramiko_level = logging.WARNING
logging.getLogger("paramiko.transport").setLevel(paramiko_level)

from config import REGISTRY
from ssh import get_ssh_client
from utils import set_homeassistant_state, get_timestamp


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

    def collect_version_info(self, latest_version):
        logger.debug(f"Collecting version info for container: {self.app} on {self.host}")
        self.latest_version = latest_version
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
            logging.error(e)
            self.current_version = None

    def get_current_version_by_docker_tag(self):
        client = get_ssh_client(self.host)
        command="/usr/bin/docker ps --format '{{json .Image}}' -f " +  f"name={self.app}"
        logger.debug(f"Executing command: {command} on {self.host}")
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode("utf-8")
        if REGISTRY in output:
            output=output.split(":")[2].split('"')[0]
        else:
            output=output.split(":")[1].split('"')[0]
        return output.strip()

    def get_frigate_current_version(host):
        sensor_value=get_state("update.frigate_server")
        return sensor_value['attributes']['installed_version']

    def get_webssh_current_version(self):
        client = get_ssh_client(self.host)
        command="/usr/bin/docker exec webssh /usr/local/bin/python /code/run.py --version"
        logger.debug(f"Using {command} to get webssh current version.")
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode("utf-8")
        logger.debug(f"Webssh current version: {output}")
        return "v" +  output.strip()

    def collect_docker_stats(self):
        logger.debug(f"Collecting docker stats for {self.app} on {self.host}")
        command = f"/usr/bin/docker ps -a --format json --filter name={self.app}"
        logger.debug(f"Executing command {command}")
        try:
            client = get_ssh_client(self.host)
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode("utf-8")
            output=json.loads(output)

            created_at=output['CreatedAt']
            image=output['Image']
            status=output['Status']
            state=output['State']

            self.container_created_at =  created_at
            self.container_state = state
            self.container_status = status
            self.container_image = image

        except Exception as e:
            logging.debug("docker ps reports no container info for " + self.app)
            self.container_created_at =  "Container Down"
            self.container_state = "Container Down"
            self.container_status = "Container Down"
            self.container_image = "Container Down"
            logger.debug(e)

    def send_single_state(self, attribute, data, sensor_attributes=None):
        short_host = self.host.split("-")[1]
        sensor_name = f'sensor.{short_host}_{self.app}_{attribute}'
        payload = {}
        payload['state'] = data
        if sensor_attributes is None:
            sensor_attributes = {}
            sensor_attributes['collection_timestamp'] = self.collection_timestamp
            payload['attributes'] = sensor_attributes
        else:
            payload['attributes'] = sensor_attributes
        set_homeassistant_state(sensor_name, payload)

    def send_state_data(self):
        logger.info(f"Sending state data for {self.app} on {self.host}")
        self.send_single_state("current_version", self.current_version)
        self.send_single_state("collection_timestamp", self.collection_timestamp)
        self.send_single_state("created_at", self.container_created_at)
        self.send_single_state("state", self.container_state)
        self.send_single_state("status", self.container_status)
        self.send_single_state("image", self.container_image)

        version_info = self.current_version if self.current_version == self.latest_version else f"( ↑ {self.latest_version} ↑ ) {self.current_version}"
        icon = "mdi:check" if self.current_version == self.latest_version else "mdi:package-down"
        attributes = {}
        attributes['icon'] = icon
        attributes['collection_timestamp'] = self.collection_timestamp
        self.send_single_state("version_info", version_info, attributes)
