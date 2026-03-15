import logging
import re
import requests
import socket
import urllib3

from config import Configuration

from concurrent.futures import ThreadPoolExecutor
from flask import Blueprint, flash, render_template, redirect, request, url_for, jsonify

configuration = Configuration()
logger = logging.getLogger(__name__)
logger.propagate = True

scheduler_config_bp = Blueprint('scheduler_config', __name__, template_folder='../../scheduler_config')

@scheduler_config_bp.route('/index')
def index():
    SCHEDULER_HOSTS = ["ubuntu-one", "raspberry-slate", "ubuntu-main", "raspberry-pearl", "raspberry-five"]
    with ThreadPoolExecutor(max_workers=len(SCHEDULER_HOSTS)) as executor:
        dict_results = executor.map(fetch_scheduler_data, SCHEDULER_HOSTS)
    results = {host: data for host, data in dict_results}
    return render_template('scheduler_config/index.html', results=results)

def fetch_scheduler_data(host):
    """Worker function to handle a single request."""
    url = f"http://{host}:5555/api/v1/scheduler_info"
    try:
        response = requests.get(url, timeout=1.75)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Successfully fetched data from {host}")
        return host, data
    except Exception as e:
        logger.warning(f"Failed to reach {host}: {e}")
        return host, {}