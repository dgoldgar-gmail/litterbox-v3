import logging
import os
import json
import logging
import signal
import socket
import yaml

from flask import Flask, request, jsonify, render_template, redirect, url_for, flash

from log_level_config_manager import LogLevelConfigManager

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO').upper())

from routes.api.v1.info import api_v1_info_bp

from routes.ansible import ansible_bp
from routes.applications import applications_bp
from routes.git_manager import git_manager_bp
from routes.icloud import icloud_bp
from routes.jinja import jinja_bp
from routes.json_editor import json_editor_bp
from routes.logging_config import logging_config_bp
from routes.registry import registry_bp
from routes.test import test_bp
from routes.scheduler_config import scheduler_config_bp
from utils import get_sync_photos
from config import Configuration

from werkzeug.middleware.proxy_fix import ProxyFix

log_level_config_manager = LogLevelConfigManager()
configuration = Configuration()

app.register_blueprint(api_v1_info_bp, url_prefix='/api/v1')

if configuration.APP_MODE == "FULL":
    app.register_blueprint(ansible_bp, url_prefix='/ansible')
    app.register_blueprint(applications_bp, url_prefix='/applications')
    app.register_blueprint(git_manager_bp, url_prefix='/git_manager')
    app.register_blueprint(icloud_bp, url_prefix='/icloud')
    app.register_blueprint(jinja_bp, url_prefix='/jinja')
    app.register_blueprint(json_editor_bp, url_prefix='/json_editor')
    app.register_blueprint(logging_config_bp, url_prefix='/logging_config')
    app.register_blueprint(registry_bp, url_prefix='/registry')
    app.register_blueprint(scheduler_config_bp, url_prefix='/scheduler_config')
    app.register_blueprint(test_bp, url_prefix='/test')

# Set a secret key for flash messages (important for production)
app.secret_key = 'super_secret_key_for_json_editor'

@app.route('/')
def landing_page():
    #user = request.headers.get('X-Forwarded-User')
    return render_template(
        'landing.html')

@app.context_processor
def inject_context():
    username = request.headers.get('X-Forwarded-User', 'Guest')
    app.logger.info("USERNAME: %s", username)
    hostname = socket.gethostname()
    app.logger.info("HOSTNAME: %s", hostname)
    sync_photos=get_sync_photos(hostname)
    version=configuration.get_version()
    return dict( hostname=hostname, sync_photos=sync_photos, username=username, version=version)

signal.signal(signal.SIGUSR1, log_level_config_manager.toggle_logging_level)
logger.info(f"SIGUSR1 signal registered to toggle logging level. Initial level: {logging.getLevelName(logging.root.level)}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5555, debug=True)
