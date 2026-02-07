import json
import logging
import os
import yaml

from config import Configuration
from flask import Blueprint, flash, render_template, redirect, request, url_for, jsonify, current_app

configuration = Configuration()

json_editor_bp = Blueprint('json_editor', __name__, template_folder='../../templates')

logger = logging.getLogger(__name__)
logger.propagate = True

SCHEMA_FILE = "schema.json"

@json_editor_bp.route("/json_editor")
def index():
    type_param = request.args.get("type")  # returns None if not present
    return render_template("json_editor/index.html", config_type=type_param)


@json_editor_bp.route("/api/schema")
def get_schema():
    schema_file = None
    schema_type = request.args.get("type")
    logger.info(f"Requested schema type: {schema_type}")

    if schema_type == "unified":
        schema_file = configuration.UNIFIED_MAPPING_SCHEMA
    elif schema_type == "overview":
        schema_file = configuration.OVERVIEW_MAPPING_SCHEMA
    elif schema_type == "applications":
        schema_file =  configuration.APPLICATIONS_CONFIG_SCHEMA
    elif schema_type == "ansible_inventory":
        schema_file = configuration.ANSIBLE_INVENTORY_SCHEMA
    elif schema_type == "ansible_site":
        schema_file = configuration.ANSIBLE_SITE_SCHEMA
    # TODO:  Else throw
    #else:

    logger.info(f"Using schema file: {schema_file}")
    schema_data = configuration.load_json_data(schema_file)

    return jsonify({
        "config_type": schema_type,
        "schema_data": schema_data,
    })


@json_editor_bp.route("/api/config")
def get_config():
    # Get the query parameter
    config_type = request.args.get("type")
    mapping_data = None
    # Load the correct mapping
    if config_type == "unified":
        mapping_data = configuration.load_yaml_data(configuration.UNIFIED_MAPPING)
    elif config_type == "overview":
        mapping_data = configuration.load_yaml_data(configuration.OVERVIEW_MAPPING)
    elif config_type == "applications":
        mapping_data =  configuration.load_json_data(configuration.APPLICATIONS_CONFIG)
    elif config_type == "ansible_inventory":
        mapping_data = configuration.load_yaml_data(configuration.ANSIBLE_INVENTORY)
    elif config_type == "ansible_site":
        mapping_data = configuration.load_yaml_data(configuration.ANSIBLE_SITE)


    return current_app.response_class(
        response=json.dumps({
            "config_type": config_type,
            "mapping_data": mapping_data
        }, indent=2, sort_keys=False),
        mimetype='application/json'
    )


@json_editor_bp.route("/api/config", methods=["POST"])
def save_config():
    data = request.get_json()  # parse JSON body
    config_type = data.get("config_type")
    mapping_data = data.get("mapping_data")
    logger.debug(f"Save config file type: {config_type}")
    logger.debug(mapping_data)

    # Save YAML based on type
    if config_type == "unified":
        save_yaml_data(mapping_data, configuration.UNIFIED_MAPPING)
    elif config_type == "overview":
        save_yaml_data(mapping_data, configuration.OVERVIEW_MAPPING)
    elif config_type == "applications":
        save_json_data(mapping_data, configuration.APPLICATIONS_CONFIG)
    elif config_type == "ansible_inventory":
        save_yaml_data(mapping_data, configuration.ANSIBLE_INVENTORY)
    elif config_type == "ansible_site":
        save_yaml_data(mapping_data, configuration.ANSIBLE_SITE)

    # Return JSON for the frontend, or redirect/render if needed
    return jsonify({"status": "success", "config_type": config_type})




