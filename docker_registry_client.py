
import logging
import re
import requests

from packaging.version import Version, InvalidVersion

from config import Configuration

logger = logging.getLogger(__name__)

class DockerRegistryClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DockerRegistryClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.configuration = Configuration()

    def version_key(self, v):
        try:
            return Version(v)
        except InvalidVersion:
            return Version("0.0.0")

    def get_latest_dockerhub_release_version(self, url, version_pattern):
        return self.get_dockerhub_release_versions(url, version_pattern)[0]

    def get_dockerhub_release_versions(self, url, version_pattern):
        if "page_size" not in url:
            url = f"{url}&page_size=100" if "?" in url else f"{url}?page_size=100"
        all_images = []
        while url:
            try:
                resp = requests.get(url, timeout=10)
                if resp.status_code == 429:
                    wait_time = int(resp.headers.get("Retry-After", 5))
                    logger.warning(f"Rate limited. Sleeping for {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                resp.raise_for_status()
                data = resp.json()
                all_images.extend([e['name'] for e in data.get('results', []) if re.match(version_pattern, e['name'])])
                url = data.get('next')
                if url and "page_size=100" not in url:
                    u = urlparse(url)
                    query = parse_qs(u.query)
                    query['page_size'] = [100]  # Overwrite
                    url = urlunparse(u._replace(query=urlencode(query, doseq=True)))
            except Exception as e:
                logger.error(f"API Fetch failed: {url} -> {e}")
                break
        if not all_images:
            logger.warning(f"No matching images found for {url}")
            return [ self.configuration.UNKNOWN ]
        all_images.sort(key=self.version_key, reverse=True)
        return all_images

    def get_latest_local_registry_image_version(self, url, version_pattern):
        logger.debug(self.get_local_registry_image_versions(url, version_pattern)[0])
        return self.get_local_registry_image_versions(url, version_pattern)[0]

    def get_local_registry_image_versions(self, url, version_pattern):
        pattern = re.compile(version_pattern)
        try:
            logger.debug(f"Fetching tags for {url} with version pattern {version_pattern}")
            resp = requests.get(url, verify=False, timeout=10)
            logger.debug(f"Response for {url}: {resp}")
            resp.raise_for_status()
            tags = resp.json().get("tags", [])
            logger.debug(f"Tags for {url}: {tags}")
            if tags:
                tags=[ s for s in tags if pattern.match(s) ]
                tags.sort(key=self.version_key, reverse=True)
                logger.debug(f"Tags for {url}: {tags}")
                return tags
            else:
                return [ self.configuration.UNKNOWN ]
        except Exception as e:
            logger.error(f"No tags found for image with url '{url}' - {e}")
            return [ self.configuration.UNKNOWN ]