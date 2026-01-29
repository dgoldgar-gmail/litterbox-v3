import json
import logging
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from config import REGISTRY
from ssh import get_ssh_client
from utils import configure_logging, set_homeassistant_state, get_timestamp, dismiss_homeassistant_notification, send_homeassistant_notification

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
            logging.error(f"Error collecting current_version_info for {self.app} on {self.host}", e)
            self.current_version = None

    def get_current_version_by_docker_tag(self):
        client = get_ssh_client(self.host)
        command = (
            "/usr/bin/docker ps "
            "--format '{{json .Image}}' "
            f"-f name={self.app}"
        )
        logger.debug(f"Executing command: {command} on {self.host}")
        stdin, stdout, stderr = client.exec_command(command)
        stdout_output = stdout.read().decode("utf-8").strip()
        stderr_output = stderr.read().decode("utf-8").strip()
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            logger.warning(f"Docker command failed: {stderr_output}")
            return "UNKNOWN"
        if not stdout_output:
            logger.warning(f"No running container found for {self.app} on {self.host}")
            return "UNKNOWN"
        image = json.loads(stdout_output)
        _, _, tag = image.rpartition(":")
        return tag

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
        set_homeassistant_state(sensor_name, payload)

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
        icon = "mdi:check" if self.current_version == self.latest_version else "mdi:package-up"

        self.notify()

        icon = icon if self.current_version != "UNKNOWN" else "mdi:alert-box-outline"
        self.send_single_state("version_info", version_info, { "icon": icon } )


    def notify(self):
        unknown_version_id = f"Unknown version for {self.app} on {self.host}"
        update_version_id = f"Update available for {self.app} on {self.host}"

        if self.current_version == "UNKNOWN":
            send_homeassistant_notification(
                service="persistent_notification",
                message=unknown_version_id,
                title=unknown_version_id
            )
        elif self.current_version != self.latest_version:
            send_homeassistant_notification(
                service="persistent_notification",
                message=f"New version available for {self.app} on {self.host} - {self.latest_version}",
                title=update_version_id
            )
        else:
            dismiss_homeassistant_notification(id=unknown_version_id)
            dismiss_homeassistant_notification(id=update_version_id)