import docker
import time
import logging

logger = logging.getLogger(__name__)

class DockerDaemonClient:
    def __init__(self, retries=3, delay=2):
        self._client = None
        self.retries = retries
        self.delay = delay

    @property
    def client(self):
        """Returns a connected Docker client or None if unavailable."""
        if self._client:
            return self._client

        for i in range(self.retries):
            try:
                client = docker.from_env()
                client.ping()  # Verify connection
                self._client = client
                return self._client
            except Exception as e:
                logger.warning(f"Docker connection attempt {i+1} failed: {e}")
                if i < self.retries - 1:
                    time.sleep(self.delay)

        logger.error("Could not establish Docker daemon connection.")
        return None

    def get_container_attrs(self, name):
        """Helper to safely fetch container attributes."""
        c = self.client
        if not c:
            return None
        try:
            return c.containers.get(name).attrs
        except docker.errors.NotFound:
            return None
        except Exception as e:
            logger.debug(f"Error fetching container {name}: {e}")
            return None


