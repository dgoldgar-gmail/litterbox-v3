import ansible_runner
import json
import logging
from pathlib import Path
import requests
import threading
import time
import urllib3
import uuid

from config import Configuration
from flask import Blueprint, flash, render_template, redirect, request, url_for, jsonify

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ansible_bp = Blueprint('ansible', __name__, template_folder='../../ansible')

logger = logging.getLogger(__name__)
logger.propagate = True

configuration = Configuration()

configuration.QUEUE_DIR = Path("./ansible/queue")
configuration.QUEUE_DIR.mkdir(exist_ok=True)

@ansible_bp.route('/hosts')
def hosts():
    mapping_data = configuration.load_yaml_data(configuration.ANSIBLE_INVENTORY)
    return render_template('ansible/hosts.html', inventory=mapping_data)

@ansible_bp.route('/roles')
def roles():
    mapping_data = configuration.load_yaml_data(configuration.ANSIBLE_SITE)
    return render_template('ansible/roles.html', sites=mapping_data)

@ansible_bp.route('/provision', methods=["POST"])
def provision():
    logger.info(request.json)
    hosts = request.json.get("hosts")
    tags = request.json.get("tags")

    if hosts is not None:
        for host in hosts:
            task_file = configuration.QUEUE_DIR / f"{host}_{int(time.time())}.json"
            task_file.write_text(json.dumps({"host": host}))
    elif tags is not None:
        for tag in tags:
            task_file = configuration.QUEUE_DIR / f"{tag}_{int(time.time())}.json"
            task_file.write_text(json.dumps({"tag": tag}))
    else:
        return {"status": "error", "message": "No hosts or tags provided"}


    return {"status": "queued"}
