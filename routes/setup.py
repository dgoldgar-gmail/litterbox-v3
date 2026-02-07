import logging
import re
import requests
import urllib3

from config import Configuration
from log_level_config_manager import LogLevelConfigManager

from flask import Blueprint, flash, render_template, redirect, request, url_for, jsonify

configuration = Configuration()
log_level_config_manager = LogLevelConfigManager()

setup_bp = Blueprint('setup', __name__, template_folder='../../setup')

log_level_config_manager = LogLevelConfigManager()

logger = logging.getLogger(__name__)
logger.propagate = True

@setup_bp.route('/logging_config')
def logging_config():
    all_loggers = log_level_config_manager.get_all_loggers()
    return render_template('setup/logging.html',
        loggers=all_loggers)


@setup_bp.route('/update_loggers', methods=['PUT'])
def update_loggers():
    data = request.json
    log_level_config_manager.apply_logger_config(data)
    configuration.save_yaml_data(data, configuration.LOGGER_CONFIG)
    return {}