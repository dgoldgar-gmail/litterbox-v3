from datetime import datetime, timedelta
import logging
import signal
import sys
import threading
from apscheduler.schedulers.blocking import BlockingScheduler
from tasks.collector import collect_host_info, collect_application_info, collect_certificate_info
from tasks.duck_dns import update_dns_info
from tasks.leader import LeaderElector
from tasks.leader import leadership_watchdog
from utils import configure_logging

from config import COLLECT_APP_INFO_INTERVAL, COLLECT_HOST_INFO_INTERVAL, COLLECT_CERTIFICATE_INFO_INTERVAL, UPDATE_DUCK_DNS_INTERVAL

LOG_LEVEL_MAP = {
    logging.INFO: 'DEBUG',
    logging.DEBUG: 'INFO'
}

logger = logging.getLogger(__name__)
configure_logging()

scheduler = BlockingScheduler()

elector = LeaderElector()
elector.start()

scheduler.add_job(
    collect_application_info,
    'interval',
    minutes=COLLECT_APP_INFO_INTERVAL,
    next_run_time=datetime.now() + timedelta(seconds=30),
    id="app_info" )
scheduler.add_job(
    collect_host_info,
    'interval',
    minutes=COLLECT_HOST_INFO_INTERVAL,
    next_run_time=datetime.now(),
    id="host_info")

scheduler.add_job(
    update_dns_info,
    'cron',
    minute=0,
    hour=f'*/{UPDATE_DUCK_DNS_INTERVAL}',
    id="duckdns_update")

scheduler.add_job(
    collect_certificate_info,
    'cron',
    minute=0,
    hour=f'*/{COLLECT_CERTIFICATE_INFO_INTERVAL}',
    id="certificate_inf")


def shutdown(signum, frame):
    logger.info(f"Received signal {signum}, shutting down scheduler...")
    scheduler.shutdown(wait=False)
    sys.exit(0)

def toggle_logging_level(signum, frame):
    current_level = logging.root.level
    new_level_name = LOG_LEVEL_MAP.get(current_level, 'DEBUG')
    new_level = getattr(logging, new_level_name.upper(), logging.INFO)

    logging.root.setLevel(new_level)
    logger.setLevel(new_level)
    for handler in logging.root.handlers:
        handler.setLevel(new_level)

    logger.error(f"!!! Logging level dynamically switched to: {new_level_name} !!!")

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

threading.Thread(
    target=leadership_watchdog,
    args=(elector, scheduler),
    daemon=True
).start()

signal.signal(signal.SIGUSR1, toggle_logging_level)
logger.info(f"SIGUSR1 signal registered to toggle logging level. Initial level: {logging.getLevelName(logging.root.level)}")

scheduler.start(paused=True)


