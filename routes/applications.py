import json
import logging
import os
import re
import requests
import subprocess
import time

from config import APPLICATIONS_CONFIG, REGISTRY
from flask import Blueprint, flash, render_template, redirect, request, url_for, jsonify, Response
from utils import load_json_data, resolve_secrets
from ssh import get_ssh_client

applications_bp = Blueprint('applications', __name__, template_folder='../../templates')

logger = logging.getLogger(__name__)
logger.propagate = True

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
    logger.info(f"Streaming log for {container_name} on {host}")
    command = f"docker logs --tail 10 -f {container_name}"
    logger.info(command)
    return generate_response(host, command)

@applications_bp.route('/restart_app', methods=['GET'])
def restart_app():
    host = request.args.get('host')
    container_name = request.args.get('container')
    command = f"docker restart {container_name}"
    return Response(generate_response(host, command), mimetype='text/plain')

@applications_bp.route('/deploy_app_version', methods=['GET'])
def deploy_app_version():
    logger.info(request.args)
    host = request.args.get('host')
    container_name = request.args.get('container')
    version = request.args.get('version')
    config = get_container_config(container_name)

    docker_image = config.get("docker", {}).get("image")

    pull_command = f"docker pull {docker_image}:{version}"
    rm_command = f"docker rm -f {container_name}"
    run_command = build_run_command(config, version)
    post_install_commands = get_post_install_commands(config, container_name)

    logger.info(pull_command)
    logger.info(rm_command)
    logger.info(run_command)
    logger.info(post_install_commands)

    commands = [
        pull_command,
        rm_command,
        run_command ]
    commands.extend(post_install_commands)
    return generate_responses(host, commands )

@applications_bp.route('/get_container_versions', methods=['GET'])
def get_container_versions():
    logger.info(request.args)
    url = request.args.get('url')
    max_pages = request.args.get('max_pages')
    version_pattern = request.args.get('version_pattern')
    if REGISTRY in url:
        return query_local_registry(url, version_pattern)
    else:
        return query_docker_hub(url, max_pages, version_pattern)

def generate_response(host, command):

    client = get_ssh_client(host)
    stdin, stdout, stderr = client.exec_command(command)

    for line in iter(stdout.readline, ""):
        yield line

    if stdout.channel.recv_exit_status() != 0:
        yield f"\nFAILURE: '{command}' failed. Stopping chain.\n"
        raise RuntimeError("Command failed: " + command)

def generate_responses( host, commands):
    try:
        for command in commands:
            yield from generate_response(host, command)
    except RuntimeError:
        return

def query_docker_hub(url,  max_version_query_pages, version_pattern):
    pattern = re.compile(version_pattern)
    all_images=[]
    curl_count=0
    logger.info(f"Querying Docker Hub...{url}")
    while url != None and curl_count < int(max_version_query_pages):
        curl_count = curl_count+1
        resp = requests.get(url)
        data = resp.json()
        images=data['results']
        images = [e['name'] for e in images]
        all_images.extend([ s for s in images if pattern.match(s) ])
        url = data['next']
    all_images.sort(reverse=True)
    return all_images


def query_local_registry(url, version_pattern):
    pattern = re.compile(version_pattern)
    logger.info(f"Querying Docker Hub...{url}")
    resp = requests.get(url, verify='/etc/docker/certs.d/192.168.50.15:5000/ca.crt')
    data = resp.json()
    images=data['tags']
    images.sort(reverse=True)
    return images

def pull_container_version(container_name, version, host):

    logger.info(f"Running upgrade of {container_name} to {version} on {host}")
    command = f"docker pull {container_name}:{version}"
    return Response(generate_response(host, command), mimetype='text/plain')

# Maybe move some stuff to a utils that can be consumed by a collector/producer for ha.
def get_current_version_by_docker_tag(apphost, container_name):
    command_array=["/usr/bin/docker", "ps", "--format", '"{{json .Image}}"', "-f",  f"name={container_name}" ]
    client = get_ssh_client(apphost)
    stdin, stdout, stderr = client.exec_command(command_array, get_pty=True, bufsize=0)
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')


def get_container_config(name):
    applications = load_json_data(APPLICATIONS_CONFIG)
    for item in applications:
        if item.get("name") == name:
            return item
    return None

def build_run_command(config, desired_verison):

    docker_info=config['docker']
    docker_image=docker_info['image']
    container_specific_args=docker_info['args']
    container_specific_args = resolve_secrets(" ".join(container_specific_args))

    common_args = [ "docker", "run", "-d", "--name", config['name'], "--network=host", "--privileged", "--restart=unless-stopped" ]

    if 'entrypoint' in docker_info:
        entrypoint = docker_info['entrypoint']
        entry_point_base = [ "--entrypoint", entrypoint[0]]
        common_args = common_args + entry_point_base

    command_array=common_args+[container_specific_args]+[docker_image+":" + desired_verison]

    if 'entrypoint' in config and len(config['entrypoint']) > 1:
        command_array = command_array + config['entrypoint'][1:]

    if 'container_args' in docker_info:
        container_args = docker_info['container_args']
        command_array = command_array + container_args
    return " ".join(command_array)


def get_post_install_commands(config, appname):
    docker_info=config['docker']
    commands = []
    if "post-startup-cmds" in docker_info:
        post_install_commands = docker_info['post-startup-cmds']
        for cmd_key in post_install_commands:
            docker_command_array = [ "docker", "exec", appname ]
            command_array = docker_command_array + post_install_commands[cmd_key]
            commands.append(" ".join(command_array))
    return commands


