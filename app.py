import logging
import os
import json
import logging
import signal
import yaml

from flask import Flask, request, jsonify, render_template, redirect, url_for, flash

from log_level_config_manager import LogLevelConfigManager

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO').upper())

from routes.ansible import ansible_bp
from routes.applications import applications_bp
from routes.git_manager import git_manager_bp
from routes.jinja import jinja_bp
from routes.json_editor import json_editor_bp
from routes.registry import registry_bp
from routes.setup import setup_bp
from routes.test import test_bp

from werkzeug.middleware.proxy_fix import ProxyFix

log_level_config_manager = LogLevelConfigManager()

app.register_blueprint(ansible_bp, url_prefix='/ansible')
app.register_blueprint(applications_bp, url_prefix='/applications')
app.register_blueprint(git_manager_bp, url_prefix='/git_manager')
app.register_blueprint(jinja_bp, url_prefix='/jinja')
app.register_blueprint(json_editor_bp, url_prefix='/json_editor')
app.register_blueprint(registry_bp, url_prefix='/registry')
app.register_blueprint(setup_bp, url_prefix='/setup')
app.register_blueprint(test_bp, url_prefix='/test')

# Set a secret key for flash messages (important for production)
app.secret_key = 'super_secret_key_for_json_editor'

@app.route('/')
def landing_page():
    #user = request.headers.get('X-Forwarded-User')
    return render_template(
        'landing.html')

@app.context_processor
def inject_user():
    username = request.headers.get('X-Forwarded-User', 'Guest')
    app.logger.info("USERNAME: %s", username)
    return dict(username=username)

signal.signal(signal.SIGUSR1, log_level_config_manager.toggle_logging_level)
logger.info(f"SIGUSR1 signal registered to toggle logging level. Initial level: {logging.getLevelName(logging.root.level)}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5555, debug=True)
