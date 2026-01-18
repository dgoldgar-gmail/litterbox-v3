
import json
import logging
import os
import re
import requests
import socket
import subprocess
import sys

from .Container import Container

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from config import UNIFIED_MAPPING
from ssh import get_ssh_client
from utils import load_yaml_data, get_timestamp, set_homeassistant_state

logger = logging.getLogger(__name__)

# TODO:  Fix logging setup...
#paramiko_level = logging.DEBUG if debug else logging.WARNING
paramiko_level = logging.WARNING
logging.getLogger("paramiko.transport").setLevel(paramiko_level)

mapping_data = load_yaml_data(UNIFIED_MAPPING)

class Host:
    def __init__(self, name):
        logger.debug(f"Initializing host: {name}")
        self.name = name
        self.host_meta = self.get_metadata()
        self.type = self.host_meta['type']
        self.temp = None
        self.volts = None
        self.nvme_device_names = self.host_meta['nvme_devices']
        self.mount_names = self.host_meta['mounts']
        self.nvme_devices = {}
        self.mounts = {}
        self.containers = {}
        self.sensors = None

    def get_metadata(self):
        mapping = load_yaml_data(UNIFIED_MAPPING)
        for map in mapping['hosts']:
            if map['name'] == self.name:
                return map

    def collect_host_info(self):
        self.collection_timestamp = get_timestamp()
        self.ping_host()
        self.type = self.host_meta['type']
        self.temp = None
        self.volts = None
        if self.status == "up":
            self.collect_mounts()
            if self.type == "raspberry-pi":
                self.temp = self.get_vcgencmd_measurement("measure_temp")
                self.volts = self.get_vcgencmd_measurement("measure_volts")
            elif self.type == "ubuntu":
                self.collect_nvme_devices()
                self.collect_sensors()

    def collect_nvme_devices(self):
        if self.nvme_device_names is None:
            return

        for device_name in self.nvme_device_names:
            try:
                self.nvme_devices[device_name] = self.collect_nvme_metrics(device_name)
            except Exception:
                logger.exception(
                    f"Failed to collect nvme metrics for {device_name} on {self.name}"
                )

    def collect_mounts(self):
        if self.mount_names is None:
            return
        for mount_name in self.mount_names:
            try:
                self.mounts[mount_name] = self.collect_smartctl_metrics(mount_name)
            except Exception:
                logger.error(f"Failed to collect smartctl metrics for mount {mount_name} on {self.name}")


    def get_json(self):
        output={}
        output['name'] = self.name
        output['collection_timestamp'] = self.collection_timestamp
        output['status'] = self.status
        output['type'] = self.type
        try:
            output['temp'] = self.temp
            output['volts'] = self.volts
            #output['sensors'] = self.sensors
            output['mounts'] = self.mounts
            output['nvme_devices'] = self.nvme_devices
        except:
            pass
        return output


    def ping_host(self):
        try:
            with socket.create_connection((self.name, 22), timeout=2):
                self.status = "up"
        except (socket.timeout, ConnectionRefusedError, OSError):
            self.status = "down"
        logger.debug(f"ping_host: {self.name} is {self.status}")

    def get_vcgencmd_measurement(self, measurement):
        client = get_ssh_client(self.name)
        command="/usr/bin/vcgencmd " +  measurement
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode("utf-8")
        sensor_value = (output.split("=")[1]).replace("'C","").replace("V","")
        logging.debug(f"get_vcgencmd_measurement {sensor_value}")
        return sensor_value.strip()

    def collect_nvme_metrics(self, device):
        client = get_ssh_client(self.name)

        command="/usr/bin/sudo /usr/sbin/nvme smart-log " + device + " -o json"
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode("utf-8")
        return json.loads(output)

    def collect_smartctl_metrics(self, mount):
        client = get_ssh_client(self.name)
        smartctl_metrics = {}
        smartctl_metrics['name'] = mount
        try:
            command="/usr/bin/sudo /usr/sbin/smartctl -A " + mount + " -j"
            logger.debug(f"Using command {command} to collect {mount} on {self.name}")
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode("utf-8")
            output = json.loads(output)
            for attr in output['ata_smart_attributes']['table']:
                logger.debug(f"{attr['name']} => {attr['value']}")
                attr_name = attr['name']
                attr_value = attr['value']
                smartctl_metrics[attr_name] = attr_value
            logger.debug(f"smartctl_metrics: {smartctl_metrics}")
            return smartctl_metrics
        except:
            logging.info("smartctl data collection failed for host " + self.name)
        return smartctl_metrics

    def collect_container_info(self, app, latest_version):
        logger.debug(f"-> collect_container_info for {app} on {self.name}, latest version: {latest_version}")
        if app in self.containers:
            container = self.containers[app]
        else:
            container = Container(self.name, app)
            self.containers[app] = container
        try:
            container.collect_version_info(latest_version)
        except:
            logger.error(f"Failed to collect version info for {app} on ${self.name}")
        try:
            container.collect_docker_stats()
        except:
            logger.error(f"Failed to collect docker stats for {app} on {self.name}")

    def collect_sensors(self):
        client = get_ssh_client(self.name)
        command="/usr/bin/sensors -j"
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode("utf-8")
        output = json.loads(output)
        logger.debug(f"Sensors {json.dumps(output)}")
        self.sensors = output

    def send_state_data(self):
        sensor_name = f"sensor.host_{self.name.replace('-', '_')}"

        payload = {}
        payload['state'] = self.status
        attributes = {}
        payload['attributes'] = attributes
        attributes['timestamp'] = self.collection_timestamp
        attributes['type'] = self.type
        attributes['cpu_temp'] = self.temp
        attributes['cpu_volts'] = self.volts
        set_homeassistant_state(sensor_name, payload)

        for container in self.containers:
            logger.debug(f"Calling send_state_data for {container} on {self.name}")
            try:
                container_obj = self.containers[container]
                logger.debug(f"Container object: {container_obj.get_json()}")
                container_obj.send_state_data()
            except Exception as e:
                logger.error(f"Failed to send state data for {container} on {self.name}: {e}")
