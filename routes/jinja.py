import logging
import os
import re
import yaml

from config import JINJA_TEMPLATES, OVERVIEW_MAPPING, UNIFIED_MAPPING, GENERATED, SECRETS_YAML
from datetime import datetime
from flask import Blueprint, flash, render_template, redirect, request, url_for, jsonify
from werkzeug.utils import safe_join
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from utils import load_yaml_data, save_yaml_data, get_secret, build_file_tree, resolve_secrets

jinja_bp = Blueprint('jinja', __name__, template_folder='../../jinja')

logger = logging.getLogger(__name__)
logger.propagate = True

files = sorted(os.listdir(JINJA_TEMPLATES))

@jinja_bp.route('/editor')
def editor():
    template_files = build_file_tree(JINJA_TEMPLATES)
    logger.info(files)
    return render_template('jinja/editor.html', template_files=template_files)


@jinja_bp.route('/resolver')
def resolver():
    mapping_data = load_yaml_data(UNIFIED_MAPPING)

    template_files = sorted(os.listdir(JINJA_TEMPLATES))

    return render_template('jinja/resolver.html',
                           mapping_data=mapping_data,
                           template_files=template_files,
                           resolverType=None,
                           resolverOption=None,
                           result=yaml.dump({}))

@jinja_bp.route('/generated')
def generated():
    generated_files = build_file_tree(GENERATED)

    return render_template('jinja/generated.html',
                           generated_files=generated_files)

@jinja_bp.route('/get-template')  # Use .route, not .read_template
def get_template():
    relative_path = request.args.get('path')
    if not relative_path:
        abort(400, "Path is required")

    try:
        full_path = safe_join(JINJA_TEMPLATES, relative_path)
    except ValueError:
        abort(400, "Invalid path")

    if os.path.exists(full_path) and os.path.isfile(full_path):
        with open(full_path, 'r') as f:
            return f.read()

    abort(404, "Template not found")


@jinja_bp.route('/get-generated-file')
def get_generated_file():
    relative_path = request.args.get('path')
    if not relative_path:
        abort(400, "Path is required")

    try:
        full_path = safe_join(GENERATED, relative_path)
    except ValueError:
        abort(400, "Invalid path")

    if os.path.exists(full_path) and os.path.isfile(full_path):
        with open(full_path, 'r') as f:
            return f.read()

    abort(404, "Generated file not found")

@jinja_bp.route('/generate', methods=['GET'])
def generate():
    template_files = sorted(os.listdir(JINJA_TEMPLATES))
    mapping_data = load_yaml_data(UNIFIED_MAPPING)
    resolver_type = request.args.get('resolverType')
    resolver_option = request.args.get('resolverOption')
    if resolver_type == "nginx":
        if "Select" in resolver_option:
            handle_error("No nginx config type given.")
        else:
            result = render_jinja_template("nginx_" + resolver_option + ".j2", mapping_data)
    elif resolver_type == "dashboards":
        result = build_dashboard()
    elif resolver_type == "homeassistant":
        result = render_jinja_template("homeassistant_" + resolver_option + ".j2", mapping_data)
    elif  resolver_type == "sshconfig" or resolver_type == "frigate":
        result = render_jinja_template(resolver_type + ".j2", mapping_data)
    else:
        result = "Error. No template type given"

    if "Error" in result:
        handle_error(result)
    else:
        flash("Template generation complete.", "success")

    return render_template('jinja/resolver.html', mapping_data=mapping_data, template_files=template_files, resolverType=resolver_type, resolverOption=resolver_option, result=result )

@jinja_bp.route('/save', methods=['POST'])
def save():

    mapping_data = load_yaml_data(UNIFIED_MAPPING)

    content = request.form['content']
    resolver_type = request.form['resolverType']
    resolver_option = request.form['resolverOption']

    logger.info(f"Saving {resolver_type} {resolver_option}")

    filename=None
    if resolver_type == "nginx" and resolver_option:
      Path(f"{GENERATED}/nginx").mkdir(parents=True, exist_ok=True)
      filename = f"{GENERATED}/nginx/{resolver_option}"
    elif resolver_type == "homeassistant":
        Path(f"{GENERATED}/homeassistant/config/yaml").mkdir(parents=True, exist_ok=True)
        filename = f"{GENERATED}/homeassistant/config/yaml/{resolver_option}"
    elif resolver_type == "dashboards":
        Path(f"{GENERATED}/homeassistant").mkdir(parents=True, exist_ok=True)
        filename = f"{GENERATED}/homeassistant/dashboard.yaml"
    elif  resolver_type == "sshconfig":
        Path(f"{GENERATED}/{resolver_type}").mkdir(parents=True, exist_ok=True)
        filename = f"{GENERATED}/{resolver_type}/config"
    elif resolver_type == "frigate":
        Path(f"{GENERATED}/{resolver_type}").mkdir(parents=True, exist_ok=True)
        filename = f"{GENERATED}/{resolver_type}/config.yaml"

    logger.info(f"Resolved filename: {filename}")

    if filename == None:
        flash(f"Save failed! Unable to resolve filename for template type {resolver_type}", "error")
    else:
        try:
            with open(filename, 'w') as f:
                content = content.replace('\r\n', '\n')
                f.write(content)
            logger.info(f"Successfully saved file {filename}")
            flash(f"Successfully saved file {filename}!","success")
        except Exception as e:
            flash(f"Failed to save {filename}", "error")

    template_files = sorted(os.listdir(JINJA_TEMPLATES))

    return render_template('jinja/resolver.html', mapping_data=mapping_data, template_files=template_files, resolverType=resolver_type, resolverOption=resolver_option )

def render_jinja_template(name, config_data):
    try:
        environment = Environment(loader=FileSystemLoader(JINJA_TEMPLATES))
        template = environment.get_template(name)

        now = datetime.now()
        environment.globals['timestamp'] = now.strftime("%Y-%m-%d %H:%M:%S")

        output=template.render(config_data)
        output=resolve_secrets(output)
        return output
    except Exception as e:
        message = "Failed rendering template!"
        handle_error(message, e)

def get_yaml_from_string(input):
    return yaml.safe_load(input)

def render_yaml_configuration(template_name):
    try:
        mapping_data = load_yaml_data(UNIFIED_MAPPING)
        if template_name == "overview_view.j2":
            overview_data = load_yaml_data(OVERVIEW_MAPPING)
            output=render_jinja_template(template_name, overview_data)
        else:
            output=render_jinja_template(template_name, mapping_data)
        return get_yaml_from_string(output)
    except Exception as e:
        message = "Rendering yaml configuration failed!"
        handle_error(message, e)

def build_dashboard():
    try:
        dashboard = {}
        views = []
        dashboard['views'] = views

        overview_view = render_yaml_configuration("overview_view.j2")
        manage_view  = render_yaml_configuration("manage_view.j2")
        notifications_view  = render_yaml_configuration("notifications_view.j2")
        tasmota_view = render_yaml_configuration("tasmota_view.j2")
        battery_view = render_yaml_configuration("battery_view.j2")
        thermometer_view = render_yaml_configuration("thermometer_view.j2")

        views.append(overview_view)
        views.append(manage_view)
        views.append(tasmota_view)
        views.append(battery_view)
        views.append(thermometer_view)
        views.append(notifications_view)
        return yaml.dump(dashboard, sort_keys=False)
    except Exception as e:
        message = "Dashboard rendering failed!"
        handle_error(message, e)

def handle_error(message, e=None):
    mapping_data = load_yaml_data(UNIFIED_MAPPING)
    logger.exception(f"Error during operation. {message}")
    if e == None:
        flash(f"Error: {message}", "error")
    else:
        flash(f"Error: {message} => {str(e)} ", "error")
    return render_template('jinja/resolver.html', mapping_data=mapping_data, files=files, result=message)


