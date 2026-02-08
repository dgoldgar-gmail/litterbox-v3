import logging
import re
import requests
import urllib3

from config import LOGGER_CONFIG
from utils import get_local_registry_image_versions, get_all_loggers, apply_logger_config, save_yaml_data
from flask import Blueprint, flash, render_template, redirect, request, url_for, jsonify

setup_bp = Blueprint('setup', __name__, template_folder='../../setup')

logger = logging.getLogger(__name__)
logger.propagate = True

@setup_bp.route('/logging_config')
def logging_config():
    all_loggers = get_all_loggers()
    return render_template('setup/logging.html',
        loggers=all_loggers)


@setup_bp.route('/update_loggers', methods=['PUT'])
def update_loggers():
    data = request.json
    apply_logger_config(data)
    save_yaml_data(data, LOGGER_CONFIG)
    return {}