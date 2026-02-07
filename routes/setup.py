import logging
import re
import requests
import urllib3

from utils import get_local_registry_image_versions, get_all_loggers
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
    logger.info("Updating loggers")
    data = request.json
    logger.info(data)
    for entry in data:
            name = entry.get('name')
            level = entry.get('level')
            if name and level:
                the_logger = logging.getLogger(name)
                the_logger.setLevel(level.upper())
                the_logger.propagate = True
                print(f"Set {name} to {level}")
    # TODO:  Probably need some try catch and send back success/failure....
    return {}