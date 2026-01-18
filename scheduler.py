from datetime import datetime, timedelta
import logging
import signal
import sys
from apscheduler.schedulers.blocking import BlockingScheduler
from tasks.collector import collect_host_info, collect_application_info
from tasks.duck_dns import update_dns_info
from config import COLLECT_APP_INFO_INTERVAL, COLLECT_HOST_INFO_INTERVAL, UPDATE_DUCK_DNS_INTERVAL

scheduler = BlockingScheduler()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)

scheduler.add_job(collect_application_info, 'interval', minutes=COLLECT_APP_INFO_INTERVAL, next_run_time=datetime.now() + timedelta(seconds=15), id="app_info" )
scheduler.add_job(collect_host_info, 'interval', minutes=COLLECT_HOST_INFO_INTERVAL, next_run_time=datetime.now(), id="host_info")
scheduler.add_job(update_dns_info, 'cron', minute=0, hour='*/12', id="duckdns_update")

def shutdown(signum, frame):
    logger.info(f"Received signal {signum}, shutting down scheduler...")
    scheduler.shutdown(wait=False)
    sys.exit(0)

# Catch termination signals
signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

if __name__ == "__main__":
    logger.info("Starting scheduler...")
    scheduler.start()

