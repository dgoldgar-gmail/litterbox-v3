import json
import logging
import socket
import ssl

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timezone
from ssl import DER_cert_to_PEM_cert

from utils import get_all_hosts, get_timestamp
from config import APPLICATIONS_CONFIG
from utils import configure_logging, load_json_data, set_homeassistant_state, dismiss_homeassistant_notification, send_homeassistant_notification

from .model.Application import Application
from .model.Host import Host

logger = logging.getLogger(__name__)
configure_logging()

cached_apps = {}
cached_hosts = {}

def collect_host_info():
    hosts=get_all_hosts()
    for host in hosts:
        try:
            if host in cached_hosts:
                host_obj = cached_hosts[host]
            else:
                host_obj = Host(host)
                cached_hosts[host] = host_obj
            host_obj.collect_host_info()
            host_obj.send_state_data()
        except Exception as e:
            logger.error(f"Failed to collect host info for {host}: {e}")

def collect_application_info():
    applications = load_json_data(APPLICATIONS_CONFIG)
    for app in applications:
        if app['platform'] == "docker" and app['live'] == "True":
            app_name = app['name']
            logger.debug(f"Collect info for: {app['name']}")
            try:
                if app_name in cached_apps.keys():
                    logger.debug(f"Getting application {app_name} from cache")
                    app_obj = cached_apps[app_name]
                else:
                    logger.debug(f"Creating application {app_name} and adding to cache ")
                    app_obj = Application(app)
                    cached_apps[app_name] = app_obj
                try:
                    app_obj.get_latest_app_version()
                except:
                    logger.error(f"Failed to get latest app version for {app_name}")
                for host in app['hosts']:
                    if host in cached_hosts.keys():
                        host_obj = cached_hosts[host]
                        if host_obj and host_obj.status == "up":
                            logger.debug(f"Confirmed {host} is up. Collecting current version for {app_name}.")
                            host_obj.collect_container_info(app_name, app_obj.latest_version)
                        else:
                            # TODO:  I guess we should zero out the states for the objects we failed to collect here...
                            logger.info(f"Host {host} is down. Skipping container collection.")
                    else:
                        logger.info(f"Host {host} cached entry does not exist yet. Skipping.")

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
        send_homeassistant_notification(
            service="persistent_notification",
            message=f"{hostname} certificate expires in {days_remaining} days",
            title=f"Time to renew {hostname} certificate"
        )
        state = "warn"
        if days_remaining < 1:
            state = "error"
    else:
        dismiss_homeassistant_notification(f"Time to renew {hostname} certificate")

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
    set_homeassistant_state(sensor_name, payload)


