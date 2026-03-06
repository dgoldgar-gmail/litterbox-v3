import json
import logging
import os
import datetime
import re
import requests
import socket
import sys
import urllib3
import yaml

from datetime import datetime
from packaging.version import Version, InvalidVersion
from ansible_vault import Vault
from flask import flash, current_app
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from config import Configuration

configuration = Configuration()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)

def get_timestamp():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

def snake_to_camel(snake_str):
    return ''.join(word.capitalize() for word in snake_str.split('_'))

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

def resolve_functions(text, user_context):
    """
    text: "Mode for &host& is &getSchedulerMode(host)&"
    user_context: {"host": "aws-prod"} # This comes from the UI/User selection
    """
    logger.info(f"resolve_functions -> {user_context}")
    pattern = r"&(\w+)(?:\((.*?)\))?&"
    def mapper(match):
        name = match.group(1)
        args_str = match.group(2)
        func = globals().get(name)
        if callable(func):
            if args_str:
                raw_args = [a.strip() for a in args_str.split(',')]
                resolved_args = [user_context.get(a, a) for a in raw_args]
                return str(func(*resolved_args))
            return str(func())
        return match.group(0)
    return re.sub(pattern, mapper, text)

def getSchedulerMode(hostname):
    mapping=configuration.load_yaml_data(configuration.UNIFIED_MAPPING)
    roles=mapping['litterbox']
    logger.info(f"Roles: {roles}")
    if hostname in roles['leaders']:
        return "leader"
    elif hostname in roles['satellites']:
        return "satellite"
    else:
        return configuration.UNKNOWN

def getSyncPhotos(hostname):
    mapping=configuration.load_yaml_data(configuration.UNIFIED_MAPPING)
    for host in mapping.get('hosts', []):
        if host.get('name') == hostname:
            containers = host.get('containers', [])
            return any(c.get('name') == 'photoprism' for c in containers)

# --- Logging Helper Function ---
def configure_logging(
    level=logging.INFO,
    *,
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


