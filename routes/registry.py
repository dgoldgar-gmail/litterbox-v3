import logging
import requests
import urllib3

from config import REGISTRY
from flask import Blueprint, flash, render_template, redirect, request, url_for, jsonify

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
registry_bp = Blueprint('registry', __name__, template_folder='../../registry')

logger = logging.getLogger(__name__)
logger.propagate = True

@registry_bp.route('/')
def index():
    return render_template('registry/index.html',
                           images=get_image_list())

@registry_bp.route('/get_image_tags', methods=['GET'])
def get_image_tags():
    image_name = request.args.get('image_name')
    logger.info(f"Getting tags for image {image_name}")
    try:
        url = f"https://{REGISTRY}/v2/{image_name}/tags/list"
        resp = requests.get(url, verify=False)
        resp.raise_for_status()
        tags = resp.json().get("tags", [])
        tags = process_tags(image_name, tags)
        results = {}
        for tag in tags:
            results[tag.tag] = tag.get_json()
        return results
    except Exception as e:
        logger.error(f"Error listing tags: {e}")
        return {}

@registry_bp.route('/get_blob_info', methods=['POST'])
def get_blob_info():
    input=request.get_json()
    if input['type'] == "tag":
        return [get_blob_info_for_config_digest(input['image'], input['content_digest'])]
    else:
        logger.info(f"Getting blob info for {input}")
        content_data = []
        for tag in input['tags']:
            logger.info(f"Get stuff for {tag['image']} {tag['content_digest']} ")
            content_data.append(get_blob_info_for_config_digest(tag['image'], tag['content_digest']))
        return content_data

@registry_bp.route('/delete_tag', methods=['DELETE'])
def delete_tag():
    image_name = request.args.get('image_name')
    tag = request.args.get('tag')
    digest = request.args.get('digest')
    redirect_url = url_for('registry.index')
    logger.info(f"Digest for {image_name}:{tag} is {digest}")
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

def process_tags(image, tags):
    tag_objects = []
    for tag in tags:
        manifest, digest, content_digest, media_type = get_image_manifest(image, tag)
        tag_obj = None
        if 'manifests' in manifest:
            child_digests = []
            for m in manifest.get("manifests", []):
                d = m.get("digest")
                if d:
                    child_digests.append(d)
            tag_obj = Tag(image, "manifest", tag, content_digest, child_digests)
        else:
            tag_obj = Tag(image, "tag", tag, content_digest, [digest])
            #logger.info(manifest)
        tag_objects.append(tag_obj)
    return post_process_tag_objects(tag_objects)

def post_process_tag_objects(tag_objects):
    return_list = []
    manifests = [obj for obj in tag_objects if obj.type == "manifest"]
    tags = [obj for obj in tag_objects if obj.type == "tag"]
    for tag in tags:
        found_tag = False
        for manifest in manifests:
            if tag.digests[0] in manifest.digests:
                manifest.add_tag(tag)
                found_tag = True
            break;
        if not found_tag:
            return_list.append(tag)

    return_list.extend(manifests)
    return return_list


def safe_get(url, headers=None):
    """GET that returns Response or None (404 or other errors suppressed)."""
    try:
        r = requests.get(url, headers=headers or {}, verify=False)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r
    except requests.RequestException:
        return None


def get_image_manifest(image, ref):
    url = f"https://{REGISTRY}/v2/{image}/manifests/{ref}"
    headers = {
        "Accept": (
            "application/vnd.docker.distribution.manifest.list.v2+json, "
            "application/vnd.docker.distribution.manifest.v2+json"
        )
    }
    resp = safe_get(url, headers)
    if not resp:
        return None, None, None
    try:
        manifest = resp.json()
    except ValueError:
        manifest = None

    digest = resp.headers.get("Docker-Content-Digest") or resp.headers.get("Content-Digest")
    content_type = resp.headers.get("Content-Type", "")

    # looking for that elusive created data...
    content_digest = None
    if 'config' in manifest and 'digest' in manifest['config']:
        logger.info(manifest['config']['digest'])
        content_digest = manifest['config']['digest']

    media_type = (manifest.get("mediaType") if isinstance(manifest, dict) else None) or (
        content_type.split(";", 1)[0] if content_type else None
    )

    return manifest, digest, content_digest, media_type

class Tag:
    def __init__(self, image, type, tag, content_digest, digests):
        self.image = image
        self.type = type
        self.tag = tag
        self.url = f"https://{REGISTRY}/v2/{image}:{tag}"
        self.digests = digests
        self.content_digest = content_digest
        self.tags = []

    def get_json(self):
        return {
            "image": self.image,
            "type": self.type,
            "tag": self.tag,
            "url": self.url,
            "digests": self.digests,
            "content_digest": self.content_digest,
            "tags": [tag.get_json() for tag in self.tags]
        }

    def add_tag(self, tag):
        self.tags.append(tag)


def get_blob_info_for_config_digest(image, config_digest):
    config_url = f"https://{REGISTRY}/v2/{image}/blobs/{config_digest}"
    config_resp = requests.get(config_url, verify=False)
    config_resp.raise_for_status()
    config_data = config_resp.json()
    logger.info(config_data)
    created_date = config_data.get("created")
    logger.info(created_date)
    return config_data


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


