import logging
import re
import requests
import socket
import urllib3

from config import Configuration
from log_level_config_manager import LogLevelConfigManager

from flask import Blueprint, flash, render_template, redirect, request, url_for, jsonify

configuration = Configuration()
log_level_config_manager = LogLevelConfigManager()

logging_config_bp = Blueprint('logging_config', __name__, template_folder='../../logging_config')

log_level_config_manager = LogLevelConfigManager()

logger = logging.getLogger(__name__)
logger.propagate = True

@logging_config_bp.route('/index')
def index():
    all_loggers = log_level_config_manager.get_all_loggers()
    return render_template('logging_config/index.html',
        loggers=all_loggers)


@logging_config_bp.route('/update_loggers', methods=['PUT'])
def update_loggers():
    data = request.json
    log_level_config_manager.apply_logger_config(data)
    configuration.save_yaml_data(data, configuration.LOGGER_CONFIG)
    return {}


