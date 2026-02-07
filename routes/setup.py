import logging
import re
import requests
import urllib3

from utils import get_local_registry_image_versions, get_all_loggers
from flask import Blueprint, flash, render_template, redirect, request, url_for, jsonify

setup_bp = Blueprint('setup', __name__, template_folder='../../setup')

logger = logging.getLogger(__name__)
logger.propagate = True

@setup_bp.route('/logging')
def logging():
    all_loggers = get_all_loggers()
    return render_template('setup/logging.html',
        loggers=all_loggers)
