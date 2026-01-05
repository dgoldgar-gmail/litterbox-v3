import logging
from utils import get_all_hosts


logging.basicConfig(
    level=logging.INFO,  # set minimum level
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)

def collect_host_info():
    logger.info("Hello.  I am collecting host info")
    hosts=get_all_hosts()
    logger.info(f"Found hosts: {hosts}" )
