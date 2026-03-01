from datetime import datetime, timedelta
import logging
import os
import signal
import sys
import threading
from apscheduler.schedulers.blocking import BlockingScheduler
from tasks.collector import collect_host_info, collect_application_info, collect_certificate_info, synch_photos
from tasks.duck_dns import update_dns_info
from tasks.leader import LeaderElector
from utils import configure_logging
from log_level_config_manager import LogLevelConfigManager

from config import Configuration

configuration = Configuration()
log_level_config_manager = LogLevelConfigManager()

logger = logging.getLogger(__name__)
configure_logging()

scheduler = BlockingScheduler()
mode = os.environ.get("MODE","satellite")
logger.info(f"MODE=> {mode}")
is_leader = mode == "leader"


logger.info(f"Collector type: {mode}")

is_synch_photos = os.getenv("SYNCH_PHOTOS", "false").lower() == "true"
logger.info(f"SYNCH_PHOTOS=> {is_synch_photos}")

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

elector = None
if is_leader:
    logger.info("Starting in MAIN mode (leader election enabled)")
    elector = LeaderElector(scheduler, configuration)
    elector.start()
else:
    logger.info("Starting in SATELLITE mode (no leader election)")

scheduler.add_job(
    collect_host_info,
    'interval',
    args=[elector],
    minutes=configuration.COLLECT_HOST_INFO_INTERVAL,
    next_run_time=datetime.now(),
    id="host_info")


if is_synch_photos:
    scheduler.add_job(
        synch_photos,
        'cron',
        day=f'*/{configuration.SYNCH_PHOTOS_INTERVAL}', # Fires every N days of the month
        hour=2,                                         # Fires at 2:00 AM
        minute=0,
        id="synch_photos",
        replace_existing=True
    )

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGUSR1, log_level_config_manager.toggle_logging_level)
logger.info(f"SIGUSR1 signal registered to toggle logging level. Initial level: {logging.getLevelName(logging.root.level)}")

scheduler.start()


