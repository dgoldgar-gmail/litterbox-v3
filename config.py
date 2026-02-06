import json
import logging
import os
import yaml

logger = logging.getLogger(__name__)

def setup_directory_environment(name, default):
    value=os.environ.get(name)
    if value is None:
        if default is None:
            raise ValueError(f"Environment variable {name} is required!")
        else:
            value=default
    logger.info(f"{name} set to: {value}")

    return value

def load_config_file(variable_name, file_name, full_path=False):
    config_file = None
    if full_path:
        config_file = f"{file_name}"
    else:
        config_file = f"{CONFIG_DIR}/{file_name}"
    logger.info(f"{variable_name} set to: {config_file}")
    return config_file

UNKNOWN="UNKNOWN"

REGISTRY = "192.168.50.15:5000"

SSH_USER = os.environ.get("SSH_USER", "dgoldgar")
logger.info(f"SSH_USER set to: {SSH_USER}")

# home assistant
HOME_ASSISTANT_API_URL="https://192.168.50.14:8123/api"

KEY_FILE = os.environ.get("KEY_FILE", "/home/dgoldgar/.ssh/homeassistant")
logger.info(f"KEY_FILE set to: {KEY_FILE}")

# Directories...

BACKUP_DIR = setup_directory_environment("BACKUP_DIR", "/app/backups")
CONFIG_DIR = setup_directory_environment("CONFIG_DIR", "app/config")
JINJA_TEMPLATES = setup_directory_environment("JINJA_TEMPLATES", "app/templates")
GENERATED = setup_directory_environment("GENERATED", "app/generated")
GIT_REPO_PATH = setup_directory_environment("GIT_REPO_PATH", "/app/git")

# Files
SECRETS_YAML = load_config_file("SECRETS_YAML", "secrets.yaml")
OVERVIEW_MAPPING = load_config_file("OVERVIEW_MAPPING", "overview_mapping.yaml")
UNIFIED_MAPPING = load_config_file("UNIFIED_MAPPING", "unified_mapping.yaml")
APPLICATIONS_CONFIG = load_config_file("APPLICATIONS_CONFIG", "applications.json")

UNIFIED_MAPPING_SCHEMA = load_config_file("UNIFIED_MAPPING_SCHEMA", "unified_mapping_schema.json")
OVERVIEW_MAPPING_SCHEMA = load_config_file("OVERVIEW_MAPPING_SCHEMA", "overview_mapping_schema.json")
APPLICATIONS_CONFIG_SCHEMA = load_config_file("APPLICATIONS_CONFIG_SCHEMA", "applications_schema.json")
ANSIBLE_INVENTORY_SCHEMA = load_config_file("ANSIBLE_INVENTORY_SCHEMA", "ansible_inventory_schema.json")
ANSIBLE_SITE_SCHEMA = load_config_file("ANSIBLE_SITE_SCHEMA", "ansible_site_schema.json")

ANSIBLE_VAULT_PASS_PATH=os.environ.get("ANSIBLE_VAULT_PASS_PATH", "/app/.ansible/vault_pass")
ANSIBLE_INVENTORY = load_config_file("ANSIBLE_CONFIG", "ansible/inventory/hosts.yml", True)
ANSIBLE_SITE = load_config_file("ANSIBLE_SITE", "ansible/project/site.yml", True)

# Scheduler Configuration

COLLECT_APP_INFO_INTERVAL=int(os.environ.get("COLLECT_APP_INFO_INTERVAL",5))
COLLECT_HOST_INFO_INTERVAL=int(os.environ.get("COLLECT_HOST_INFO_INTERVAL",5))
COLLECT_CERTIFICATE_INFO_INTERVAL=int(os.environ.get("COLLECT_CERTIFICATE_INFO_INTERVAL",12))
UPDATE_DUCK_DNS_INTERVAL=int(os.environ.get("UPDATE_DUCK_DNS_INTERVAL",12))


LEADER_TTL=int(os.environ.get("LEADER_TTL",240))
LEADER_WATCHDOG_INTERVAL=int(os.environ.get("LEADER_TTL",60))
LEADER_HEARTBEAT_INTERVAL=int(os.environ.get("LEADER_TTL",60))