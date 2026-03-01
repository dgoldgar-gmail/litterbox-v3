import json
import logging
import socket
import ssl

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timezone
from pathlib import Path
from ssl import DER_cert_to_PEM_cert

from utils import get_timestamp
from config import Configuration
from home_assistant_client import HomeAssistantClient
from icloud_client import synch_photos_for_user


from .model.Application import Application
from .model.Host import Host

configuration = Configuration()
home_assistant_client = HomeAssistantClient()

logger = logging.getLogger(__name__)
#configure_logging()

cached_apps = {}
cached_hosts = {}

# TODO:  Refactor this.. it should only collect for the local host...
#        It will also need to collect the container info for the local host
#.       It will need to get the latest version from the ha-state
def collect_host_info(elector):
    hostname = socket.gethostname()
    logger.info(f"Collecting host info for {hostname}")
    try:
        host_obj = Host(hostname, elector)
        host_obj.collect_host_info()
        host_obj.send_state_data()
    except Exception as e:
        logger.error(f"Failed to collect host info for {hostname}: {e}")

def collect_application_info():
    applications = configuration.load_json_data(configuration.APPLICATIONS_CONFIG)
    for app in applications:
        if app['platform'] == "docker" and app['live'] == "True":
            app_name = app['name']
            logger.debug(f"Collect info for: {app['name']}")
            try:
                if app_name in cached_apps.keys():
                    app_obj = cached_apps[app_name]
                else:
                    app_obj = Application(app)
                    cached_apps[app_name] = app_obj
                try:
                    logger.info(f"Getting latest app version for {app_name}")
                    app_obj.get_latest_app_version()
                    latest_version = app_obj.latest_version
                    sensor_name = f"sensor.{app_name}_latest_version"
                    payload = {}
                    payload['state'] = latest_version
                    sensor_attributes = {}
                    sensor_attributes['collection_timestamp'] = get_timestamp()
                    home_assistant_client.set_homeassistant_state(sensor_name, payload)
                except:
                    logger.error(f"Failed to get latest app version for {app_name}")

            except Exception as e:
                logger.error(f"Failed to collect app info for {app_name}: {e}")

def collect_certificate_info():
    hostname="authabitrail.duckdns.org"
    port=443
    timeout=5
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    with socket.create_connection((hostname, port), timeout=timeout) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            der_cert = ssock.getpeercert(binary_form=True)

    if not der_cert:
        return {
            "hostname": hostname,
            "error": "No certificate presented"
        }

    cert = x509.load_der_x509_certificate(der_cert, default_backend())

    not_before = cert.not_valid_before.replace(tzinfo=timezone.utc)
    not_after = cert.not_valid_after.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    days_remaining = (not_after - now).days

    state = "ok"
    if days_remaining < 7:
        home_assistant_client.send_homeassistant_notification(
            service="persistent_notification",
            message=f"{hostname} certificate expires in {days_remaining} days",
            title=f"Time to renew {hostname} certificate"
        )
        state = "warn"
        if days_remaining < 1:
            state = "error"
    else:
        home_assistant_client.dismiss_homeassistant_notification(f"Time to renew {hostname} certificate")

    sensor_name = f"sensor.{hostname.replace('.', '_')}_certificate"
    payload = {}
    payload['state'] = state
    sensor_attributes = {}
    sensor_attributes['collection_timestamp'] = get_timestamp()
    sensor_attributes['hostname'] = hostname
    sensor_attributes['not_before'] = not_before.isoformat()
    sensor_attributes['not_after'] = not_after.isoformat()
    sensor_attributes['days_remaining'] = days_remaining
    sensor_attributes['subject'] = cert.subject.rfc4514_string()
    sensor_attributes['issuer'] = cert.issuer.rfc4514_string()
    sensor_attributes['serial_number'] = cert.serial_number
    payload['attributes'] = sensor_attributes
    home_assistant_client.set_homeassistant_state(sensor_name, payload)


def synch_photos():
    users = [ "dave", "erin" ]
    for user in users:
        synch_photos_for_user(user)


