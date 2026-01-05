import json
import logging
import os
import subprocess
import time

from config import APPLICATIONS_CONFIG, KEY_FILE
from flask import Blueprint, flash, render_template, redirect, request, url_for, jsonify, Response
from utils import load_json_data, save_json_data
from .applications_utils.edit import handle_save_app, launch_app_editor
from .applications_utils.manage import generate_response, query_docker_hub

applications_bp = Blueprint('applications', __name__, template_folder='../../templates')

logger = logging.getLogger(__name__)
logger.propagate = True

@applications_bp.route('/')
def index():
    applications = load_json_data(APPLICATIONS_CONFIG)
    print(applications)
    return render_template('applications/hosts.html',
                           currentApplications=applications)

@applications_bp.route('/reorder', methods=['PUT'])
def reorder():
    applications = load_json_data(APPLICATIONS_CONFIG)
    key_order = request.json

    reordered_applications = []

    for key in key_order:
        found_app =  next((item for item in applications if item["name"] == key), None)
        if found_app is not None:
            reordered_applications.append(found_app)

    save_json_data(reordered_applications, APPLICATIONS_CONFIG)
    flash(f"Applications reordered successfully!", 'success')
    return jsonify({'status': 'success', 'message': 'Applications reordered!'})

@applications_bp.route('/delete', methods=['POST'])
def delete_app():
    applications = load_json_data(APPLICATIONS_CONFIG)
    names_to_delete = request.form.getlist("application_entries")
    logger.info(names_to_delete)

    updated_applications = []
    for app in applications:
        if app["name"] in names_to_delete:
            updated_applications.append(app)

    save_json_data(updated_applications, APPLICATIONS_CONFIG)
    flash(f"{len(names_to_delete)} application(s) deleted successfully!", 'success')
    return redirect(url_for('applications.index'))

@applications_bp.route('/add_application/<name>', methods=['GET'])
def add_application(name):
    return launch_app_editor(None)

@applications_bp.route('/edit_application/<name>', methods=['GET'])
def edit_application(name):
    return launch_app_editor(name)

@applications_bp.route('/save_application', methods=['POST','PUT'])
def save_application():
    return handle_save_app(request)

@applications_bp.route('/manage_application/<name>', methods=['GET'])
def manage_application(name):
    applications = load_json_data(APPLICATIONS_CONFIG)
    logger.info("In manage_application for " + str(name))
    app_to_manage = next((item for item in applications if item["name"] == name), None)
    logger.info(app_to_manage)
    return render_template('applications/app_manager.html',                           
                           app_name=name,
                           application_config=app_to_manage)

@applications_bp.route('/stream_log', methods=['GET'])
def stream_log():
    host = request.args.get('host')
    container_name = request.args.get('container')
    command = f"docker logs --tail 10 -f {container_name}"
    resp =  Response(generate_response(host, command), mimetype='text/plain')
    resp.headers['X-Accel-Buffering'] = 'no'
    return resp

@applications_bp.route('/restart_app', methods=['GET'])
def restart_app():
    host = request.args.get('host')
    container_name = request.args.get('container')
    command = f"docker restart {container_name}"
    return Response(generate_response(host, command), mimetype='text/plain')

@applications_bp.route('/upgrade_app', methods=['GET'])
def upgrade_app():
    logger.info(request.args)
    host = request.args.get('host')
    container_name = request.args.get('container')
    version = request.args.get('version')
    command = f"/opt/LITTERBOX/bin/start_containerized_app.py {container_name} {version}"
    logger.info(f"Running upgrade of {container_name} to {version} on {host}")
    return Response(generate_response(host, command), mimetype='text/plain')

@applications_bp.route('/get_container_versions', methods=['GET'])
def get_container_versions():
    logger.info(request.args)
    url = request.args.get('url')
    max_pages = request.args.get('max_pages')
    version_pattern = request.args.get('version_pattern')
    return query_docker_hub(url, max_pages, version_pattern)
