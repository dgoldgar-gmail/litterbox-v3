import logging
import re
import requests
import urllib3

from config import REGISTRY
from utils import get_local_registry_image_versions
from flask import Blueprint, flash, render_template, redirect, request, url_for, jsonify

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
registry_bp = Blueprint('registry', __name__, template_folder='../../registry')

logger = logging.getLogger(__name__)
logger.propagate = True

@registry_bp.route('/')
def index():
    return render_template('registry/index.html', images=get_image_list())

@registry_bp.route('/get_image_tags', methods=['GET'])
def get_image_tags():
    image_name = request.args.get('image_name')
    url = f"https://{REGISTRY}/v2/{image_name}/tags/list"
    tags=get_local_registry_image_versions(url, ".*")
    logger.info(tags)
    return tags

@registry_bp.route('/get_tag_details', methods=['GET'])
def get_tag_details():
    image_name = request.args.get('image_name')
    tag = request.args.get('tag')
    return get_tag_details(image_name, tag)

@registry_bp.route('/get_architecture_manifest_details', methods=['GET'])
def get_architecture_manifest_details():
    image_name = request.args.get('image_name')
    tag = request.args.get('tag')
    manifest = request.args.get('manifest')
    return get_blob(image_name, manifest)

@registry_bp.route('/delete_tag', methods=['DELETE'])
def delete_tag():
    image_name = request.args.get('image_name')
    tag = request.args.get('tag')
    digest = request.args.get('digest')
    redirect_url = url_for('registry.index')
    url = f"https://{REGISTRY}/v2/{image_name}/manifests/{digest}"

    try:
        resp = requests.delete(url, verify=False)
        flash_status = 'success'
        if resp.status_code == 202:
            message= f"Successfully deleted {image_name}:{tag} ({digest})"
        else:
            flash_status = 'failure'
            message = f"Failed to delete tag {image_name} {tag} {digest}"
            
    except Exception as e:
        flash_status = 'failure'
        message = f"Failed to delete tag {image_name} {tag} {digest}"

    flash(message, flash_status)
    return redirect(redirect_url)

def get_image_list():
    url = f"https://{REGISTRY}/v2/_catalog"
    try:
        resp = requests.get(url, verify=False)
        resp.raise_for_status()
        return resp.json().get("repositories", [])
    except Exception as e:
        logger.error(f"Error listing images: {e}")
        return []

def safe_get(url, headers=None):
    """GET that returns Response or None (404 or other errors suppressed)."""
    try:
        logger.info(f"GET {url}")
        r = requests.get(url, headers=headers or {}, verify=False)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r
    except requests.RequestException:
        return None

def get_tag_details(image_name, tag):
    url = f"https://{REGISTRY}/v2/{image_name}/manifests/{tag}"
    headers = {
        "Accept": (
            "application/vnd.docker.distribution.manifest.list.v2+json,"
            "application/vnd.docker.distribution.manifest.v2+json,"
            "application/vnd.oci.image.manifest.v1+json,"
            "application/vnd.oci.image.index.v1+json"
        )
    }
    resp = safe_get(url, headers)
    resp_json = resp.json()
    media_type = resp_json.get("mediaType")
    results = {}
    results['image_name'] = image_name
    results['media_type'] = media_type
    results['tag'] = tag
    images = []
    results['images'] = images
    if media_type == "application/vnd.docker.distribution.manifest.list.v2+json" or media_type == "application/vnd.oci.image.index.v1+json":
        type = "OCI Multi-arch manifest"
        results['type'] = type
        results = process_multiarch_manifest_list(image_name, tag, resp_json)
    else:
        type = "Single-arch manifest"
        results['type'] = type
        result = {}
        result['digest'] = resp_json.get("config").get("digest")
        result['size'] = resp_json.get("config").get("size")
        images.append(result)
    #else:
    #    logger.warn(f"We're not handling the type of mediaType {media_type} we got here!")
    return results

def process_multiarch_manifest_list(image_name, tag, manifest_list_json):
    media_type = manifest_list_json.get("mediaType")
    if media_type == "application/vnd.docker.distribution.manifest.list.v2+json":
        type = "Multi-arch manifest"
    elif media_type == "application/vnd.oci.image.index.v1+json":
        type = "OCI Multi-arch manifest"
    results = {}
    results['image_name'] = image_name
    results['tag'] = tag
    results['type'] = type
    images = []
    results['images'] = images
    manifests = manifest_list_json.get("manifests")
    if manifests:
        type = "Multi-arch manifest OCI"
        for manifest in manifests:
            if "annotations" in manifest and manifest.get("annotations").get("vnd.docker.reference.type") ==  'attestation-manifest':
                logger.info("Skipping processing of attestation manifest.")
            else:
                result = {}
                result['arch'] = manifest.get("platform").get("architecture")
                result['os'] = manifest.get("platform").get("os")
                result['digest'] = manifest.get("digest")
                result['size'] = manifest.get("size")
                images.append(result)
                process_manifest_details(image_name, manifest)
    return results


def process_manifest_details(image_name, oci_json):
    digest = oci_json.get("digest")
    url = f"https://{REGISTRY}/v2/{image_name}/manifests/{digest}"
    headers = {
        "Accept": (
            "application/vnd.docker.distribution.manifest.v2+json, "
            "application/vnd.oci.image.manifest.v1+json"
        )
    }
    try:
        resp = safe_get(url, headers=headers)
        if resp.status_code == 200:
                manifest_data = resp.json()
                config_digest = manifest_data.get("config", {}).get("digest")
                if config_digest:
                    image_details = get_blob(image_name, config_digest)
                    container_config = image_details.get('config', {})
                    env_vars = container_config.get('Env', [])
                    entrypoint = container_config.get('Entrypoint', [])
                    labels = container_config.get('Labels', {})
                    return image_details
    except Exception as e:
        logger.error(f"Error fetching manifest {digest}: {e}")


def get_blob(image_name, digest):
    url = f"https://{REGISTRY}/v2/{image_name}/blobs/{digest}"
    try:
        resp = safe_get(url)
        if resp.status_code == 200:
            blob_data = resp.json()
            media_type = blob_data.get("mediaType")
            if media_type == "application/vnd.oci.image.manifest.v1+json":
                return get_blob(image_name, blob_data.get("config", {}).get("digest"))
            created_raw = blob_data.get('created')
            created_pretty = "Unknown"
            if created_raw:
                try:
                    dt = datetime.fromisoformat(created_raw.replace('Z', '+00:00'))
                    created_pretty = dt.strftime('%b %d, %Y %H:%M:%S')
                except Exception:
                    created_pretty = created_raw
            get_history(blob_data)
            runtime_config = blob_data.get('config', blob_data)
            details = {
                "built": created_pretty, # Our new field
                "cmd": runtime_config.get("Cmd"),
                "entrypoint": runtime_config.get("Entrypoint"),
                "env": runtime_config.get("Env"),
                "labels": runtime_config.get("Labels"),
                "working_dir": runtime_config.get("WorkingDir"),
                "user": runtime_config.get("User"),
                "exposed_ports": list(runtime_config.get("ExposedPorts", {}).keys()) if runtime_config.get("ExposedPorts") else []
            }

            #for key, value in details.items():
            #    if value and key != "built":
            #        logger.info(f"{key.replace('_', ' ').capitalize()}: {value}")

            return details
        else:
            logger.error(f"Blob not found: {resp.status_code}")
    except Exception as e:
        logger.error(f"Error fetching blob {digest}: {e}")
    return None


def get_history(blob_data):

    history = blob_data.get('history', [])
    build_steps = [step.get('created_by', '') for step in history]
    details = {
        # ... your other fields ...
        "build_history": build_steps
    }
    for i, step in enumerate(build_steps):
        clean_step = step.replace('/bin/sh -c #(nop) ', '').strip()
        logger.info(f"Step {i+1}: {clean_step}")


def format_docker_step(step_string):
    # 1. Remove the "no-op" prefix used for metadata-only commands (ENV, LABEL, etc.)
    step = step_string.replace('/bin/sh -c #(nop) ', '')

    # 2. Remove the shell execution prefix for RUN commands
    step = step.replace('/bin/sh -c ', 'RUN ')

    # 3. Clean up multiple spaces
    step = ' '.join(step.split())

    # 4. Make it look like a Dockerfile (e.g., adding line breaks for long RUN commands)
    # We look for common command separators like '&&'
    if '&&' in step:
        step = step.replace('&&', '&& \\\n  ')

    return step




############
# DOCKER INSPECT....
# docker image inspect 192.168.50.15:5000/litterbox-manager:0.5
# docker manifest inspect 192.168.50.15:5000/meatometer:0.4 - could be interesting for multi-arch images...


############################################################
# LOG LEVEL TOGGLE FOR IMAGE THAT SUPPORTS IT
#docker kill -s SIGUSR1 meatometer

##########################################################
# DELETING THE MANIFEST
#
# Delete the local manifest on the systems...
# docker manifest rm 192.168.50.15:5000/radoneye:0.6
#
#curl -sI -H "Accept: application/vnd.docker.distribution.manifest.list.v2+json" \
#    http://192.168.50.15:5000/v2/meatometer/manifests/0.4 \
#                         | grep -i 'Docker-Content-Digest'
#
# curl -X DELETE \
# http://192.168.50.15:5000/v2/meatometer/manifests/sha256:abcd...
#
# then run cleanup... note that the ai always gives the wrong config.yml path
# also note the ai wants us to stop the container which makes no sense.
# docker run --rm \
#       -v <your_storage_volume>:/var/lib/registry \
#        registry:2 garbage-collect /etc/distribution/config.yml




#####
#  get a list of images - https://{REGISTRY}/v2/_catalog
#  get a list of tags for an image - https://{REGISTRY}/v2/{image_name}/tags/list



#url = f"https://{REGISTRY}/v2/{image_name}/manifests/{digest}"
#url = f"https://{REGISTRY}/v2/{image}/manifests/{ref}"
#self.url = f"https://{REGISTRY}/v2/{image}:{tag}"
#config_url = f"https://{REGISTRY}/v2/{image}/blobs/{config_digest}"
