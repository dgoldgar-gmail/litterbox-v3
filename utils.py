import json
import logging
import os
import shutil
import datetime
import re
import requests
import sys
import yaml

from datetime import datetime
from ansible_vault import Vault
from yaml import SafeLoader, SafeDumper # Specific loaders/dumpers for safety
from flask import flash, current_app
from config import BACKUP_DIR,UNIFIED_MAPPING, HOME_ASSISTANT_API_URL

logger = logging.getLogger(__name__)

def get_timestamp():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

def snake_to_camel(snake_str):
    return ''.join(word.capitalize() for word in snake_str.split('_'))

# --- YAML Helper Functions ---
def load_yaml_data(yaml_file_path):
    """Loads YAML data from the specified file."""
    if os.path.exists(yaml_file_path):
        try:
            with open(yaml_file_path, 'r') as f:
                content = f.read()
                if content:
                    loaded_data = yaml.load(content, Loader=SafeLoader)
                    logger.info(f"Data loaded successfully from {yaml_file_path}.")
                    return loaded_data if loaded_data is not None else {}
                else:
                    logger.info(f"File {yaml_file_path} is empty. Initializing with empty data.")
                    return {}
        except yaml.YAMLError as e:
            logger.info(f"Error parsing YAML from {yaml_file_path}: {e}")
            return {}
        except Exception as e:
            logger.info(f"An unexpected error occurred loading YAML from {yaml_file_path}: {e}")
            return {}
    logger.info(f"File {yaml_file_path} not found. Initializing with empty data.")
    return {}

def save_yaml_data(app_data_dict, yaml_file_path):
    create_backup(yaml_file_path)  # Same backup logic
    try:
        with open(yaml_file_path, 'w') as f:
            yaml.safe_dump(app_data_dict, f, sort_keys=False)
            logger.info(f"YAML data saved successfully to {yaml_file_path}")
    except Exception as e:
        logger.info(f"Error saving YAML data to {yaml_file_path}: {e}")

# --- JSON Helper Functions ---

def load_json_data(json_file_path):
    with open(json_file_path, 'r') as f:
        content = f.read()
        return json.loads(content)

def save_json_data(app_data_dict, json_file_path):
    create_backup(json_file_path)  # New backup logic

    try:
        with open(json_file_path, 'w') as f:
            json.dump(app_data_dict, f, indent=2)
            logger.info(f"Data saved successfully to {json_file_path}. Saved {len(app_data_dict)} applications.")
    except Exception as e:
        logger.info(f"Error saving data to {json_file_path}: {e}")

# --- Backup Helper Function ---
def create_backup(file_path):
    if os.path.exists(file_path):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_dir = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        backup_dir = os.path.join(file_dir, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        backup_file_path = os.path.join(backup_dir, f"{file_name.replace('.', f'_{timestamp}.', 1)}")

        try:
            shutil.copyfile(file_path, backup_file_path)
            logger.info(f"Backup created: {backup_file_path}")
        except Exception as e:
            logger.info(f"Error creating backup of {file_path}: {e}")

# --- Host Helper Function ---
def get_all_hosts():
    mapping_data = load_yaml_data(UNIFIED_MAPPING)
    hosts = mapping_data['hosts']
    return  [item['name'] for item in hosts]

# --- File System Helper Function ---
def build_file_tree(base_path):
    tree = []
    for entry in sorted(os.listdir(base_path)):
        full_path = os.path.join(base_path, entry)
        if entry == "backups":
            pass
        elif os.path.isdir(full_path):
            tree.append({
                'name': entry,
                'type': 'folder',
                'children': build_file_tree(full_path)
            })
        else:
            tree.append({
                'name': entry,
                'type': 'file'
            })
    return tree

# --- Secrets Helper Function ---
def get_secrets():
    # Read the password from your pass file
    with open(".ansible/vault_pass", 'r') as f:
        password = f.read().strip()

    # Read the encrypted secrets file
    vault = Vault(password)
    with open("ansible/project/group_vars/all/secrets.yml", 'r') as f:
        return vault.load(f.read())

def get_secret(name):
    secrets = get_secrets()
    return secrets[name]

def resolve_secrets(text):
    matches=re.findall("@([^@]+)@",text)
    for match in matches:
        resolved=get_secret(match)
        logger.debug("Replace " + match + " with " + resolved)
        text=text.replace("@" + match + "@", resolved)
    return text

# --- Home Assistant Helper Functions ---
def get_homeassistant_state(name):
    url=f"{HOME_ASSISTANT_API_URL}/states/{name}"
    headers = {}
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = "Bearer " + get_secret("ha_assistant")
    logger.debug(f"Get state for {name}")
    logger.debug(f"URL: {url}")
    output=requests.get(url, headers=headers, verify=False)
    return output.json()

def set_homeassistant_state(name, payload):
    url=f"{HOME_ASSISTANT_API_URL}/states/{name}"
    headers = {}
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = "Bearer " + get_secret("ha_assistant")
    logger.debug(
        f"\n<<< {name} >>>\n%s",
        json.dumps(payload, indent=2, sort_keys=True)
    )
    r = requests.post(url , data=json.dumps(payload), headers=headers, verify=False)
    r.raise_for_status()

def send_homeassistant_notification(service, message, title=None, data=None):
    url = f"{HOME_ASSISTANT_API_URL}/services/{service}/create"
    payload = {"message": message}
    headers = {}
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = "Bearer " + get_secret("ha_assistant")
    logger.info(
        f"\n<<< ALERT >>>\n%s",
        json.dumps(payload, indent=2, sort_keys=True)
    )
    if title:
        payload['notification_id'] = title
        payload["title"] = title
    else:
        payload['title'] = message
        payload['notification_id'] = message
    # TODO: This works for persistent, but not for cell phone i think....
    if data:
        payload["data"] = data
    r = requests.post(url, headers=headers, json=payload, timeout=5, verify=False)
    r.raise_for_status()


def dismiss_homeassistant_notification(id):
    url = f"{HOME_ASSISTANT_API_URL}/services/persistent_notification/dismiss"
    payload = { "notification_id": id }
    headers = {}
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = "Bearer " + get_secret("ha_assistant")
    logger.info(
        f"\n<<< DISMISS >>>\n%s",
        json.dumps(payload, indent=2, sort_keys=True)
    )
    r = requests.post(url, headers=headers, json=payload, timeout=5, verify=False)
    r.raise_for_status()

# --- Logging Helper Function ---
def configure_logging(
    level=logging.INFO,
    *,
    silence_libs=True,
    force=False,
):
    root = logging.getLogger()
    if root.handlers and not force:
        root.setLevel(level)
        return
    root.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    handler.setFormatter(formatter)
    root.handlers.clear()
    root.addHandler(handler)

    if silence_libs:
        logging.getLogger("paramiko.transport").setLevel(logging.WARNING)
        logging.getLogger("apscheduler").setLevel(logging.INFO)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

