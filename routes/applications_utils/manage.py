
import json
import logging
import os
import re
import requests
import subprocess
import time

from config import KEY_FILE, SSH_USER
from flask import  Response
from ssh import get_ssh_client

logger = logging.getLogger(__name__)
logger.propagate = True

def generate_response(host, command):
    client = None
    try:
        client = get_ssh_client(host)
        stdin, stdout, stderr = client.exec_command(command, get_pty=True, bufsize=0)

        for line in iter(stdout.readline, ""):
            yield line

    except Exception as e:
        logger.info(f"Error during SSH stream: {e}")
        yield f"Error: {e}\n"
    finally:
        if client:
            client.close()
            logger.info("SSH client connection closed.")

def query_docker_hub(url,  max_dockerhub_pages, version_pattern):
    pattern = re.compile(version_pattern)
    all_images=[]
    curl_count=0
    logger.info(f"Querying Docker Hub...{url}")
    while url != None and curl_count < int(max_dockerhub_pages):
        curl_count = curl_count+1
        resp = requests.get(url)
        data = resp.json()
        images=data['results']
        images = [e['name'] for e in images]
        all_images.extend([ s for s in images if pattern.match(s) ])
        url = data['next']
    all_images.sort(reverse=True)

    return all_images