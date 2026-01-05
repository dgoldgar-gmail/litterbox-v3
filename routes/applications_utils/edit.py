import json
import logging
import os
import subprocess
import time

from config import APPLICATIONS_CONFIG
from flask import Blueprint, flash, render_template, redirect, request, url_for, jsonify, Response
from utils import load_json_data, save_json_data, get_all_hosts

logger = logging.getLogger(__name__)
logger.propagate = True

def launch_app_editor(app_name=None):
    app_to_edit = None
    is_edit_mode = False
    if app_name is not None:
        is_edit_mode=True
        applications = load_json_data(APPLICATIONS_CONFIG)
        app_to_edit = next((item for item in applications if item["name"] == app_name), None)

    all_hosts = get_all_hosts()

    return render_template(
        'applications/app_editor.html',
        all_hosts=all_hosts,
        app=app_to_edit,
        is_edit_mode=is_edit_mode)

def handle_save_app(request):
    applications = load_json_data(APPLICATIONS_CONFIG)

    data = request.get_json()
    name = data['name']
    logger.info(data)

    flash_message_type = "updated"

    update_applications = []
    if request.method == "PUT":
        for item in applications:
            if item["name"] == name:
                update_applications.append( data )
            else:
                update_applications.append( item )
        applications = update_applications
    else:
        flash_message_type = "added"
        applications.append( data )

    redirect_url = url_for('applications.index')
    save_json_data (applications, APPLICATIONS_CONFIG)
    flash(f"Application {name} {flash_message_type} successfully!", 'success')
    return jsonify({
        "message": "Application saved successfully!",
        "redirect_url": redirect_url
    }), 200