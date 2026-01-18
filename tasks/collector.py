import json
import logging
from utils import get_all_hosts
from config import APPLICATIONS_CONFIG
from utils import load_json_data

from .model.Application import Application
from .model.Host import Host

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)

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
                    logger.info(f"Getting application {app_name} from cache")
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
                            logger.info(f"Host {host} is down. Skipping container collection.")
                    else:
                        logger.info(f"Host {host} cached entry does not exist yet. Skipping.")

            except Exception as e:
                logger.error(f"Failed to collect app info for {app_name}: {e}")

