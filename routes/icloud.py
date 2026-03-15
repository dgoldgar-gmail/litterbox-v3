import logging
import re
import requests
import socket
import urllib3

from config import Configuration
from icloud_client import ICloudClientLockManager
from utils import get_sync_photos

from flask import Blueprint, flash, render_template, redirect, request, url_for, jsonify

configuration = Configuration()
manager = ICloudClientLockManager()

icloud_bp = Blueprint('icloud', __name__, template_folder='../../icloud')

logger = logging.getLogger(__name__)
logger.propagate = True

@icloud_bp.route('/index', methods=['GET'])
def index():
    logger.info(f"loading {configuration.ICLOUD_PHOTOS_LOCK}")
    session_data = configuration.load_json_data(configuration.ICLOUD_PHOTOS_LOCK)
    logger.info(session_data)

    return render_template('icloud/index.html',
        sessions = session_data)


@icloud_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    user = data.get('user')

    if not user:
        return jsonify({"success": False, "message": "No user provided"}), 400

    logger.info(f"Initiating login request for: {user}")

    # This triggers the first step of your library's auth flow
    status_str, client = manager.authenticate_user(user)
    # status_str will be "NEEDS_MFA", "READY", "FAILED_CREDENTIALS", etc.

    manager.reload()

    return jsonify({
        "success": True,
        "status": status_str,
        "message": f"Login process started for {user}",
        "sessions": manager.locks # Send the updated locks back to the UI
    }), 200

@icloud_bp.route('/auth/mfa', methods=['POST'])
def mfa():
    data = request.get_json()
    user = data.get('user')
    code = data.get('code')

    if not user or not code:
        return jsonify({"success": False, "message": "User and code are required"}), 400

    logger.info(f"Submitting MFA code for {user}: {code}")
    status_str, client = manager.authenticate_user(user, mfa_code=code)

    manager.reload()

    return jsonify({
        "success": status_str == "READY",
        "status": status_str,
        "message": f"MFA attempt finished with status: {status_str}",
        "sessions": manager.locks
    }), 200
