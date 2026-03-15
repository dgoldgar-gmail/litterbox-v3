import json
import logging
import os
import subprocess
import time
from flask import Blueprint, flash, render_template, redirect, request, url_for, jsonify

api_v1_info_bp = Blueprint('api/v1', __name__, template_folder='../../api/v1')

logger = logging.getLogger(__name__)
logger.propagate = True

@api_v1_info_bp.route('/scheduler_info', methods=['GET'])
def scheduler_info():
    try:
        logger.info("Signaling scheduler via local supervisorctl...")
        subprocess.run([
            "supervisorctl", "-s", "unix:///tmp/supervisor.sock",
            "signal", "SIGUSR2", "scheduler"
        ], check=True)
        time.sleep(0.1)
        status_file = "/tmp/scheduler_config.json"
        if not os.path.exists(status_file):
            return jsonify({"error": "Status file not found"}), 404
        with open(status_file, "r") as f:
            data = json.load(f)
        return jsonify(data), 200
    except subprocess.CalledProcessError as e:
        logger.error(f"Supervisor signal failed: {e}")
        return jsonify({"error": "Could not signal scheduler"}), 500
    except Exception as e:
        logger.error(f"Error reading scheduler data: {e}")
        return jsonify({"error": str(e)}), 500