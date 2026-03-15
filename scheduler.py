from datetime import datetime, timedelta
import json
import logging
import os
import signal
import sys
import threading
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.schedulers.blocking import BlockingScheduler
from tasks.collector import collect_host_info, collect_application_info, collect_certificate_info, synch_photos
from tasks.duck_dns import update_dns_info
from tasks.leader import LeaderElector
from utils import configure_logging
from log_level_config_manager import LogLevelConfigManager

from config import Configuration

configuration = Configuration()
log_level_config_manager = LogLevelConfigManager()
elector = None

logger = logging.getLogger(__name__)
configure_logging()

scheduler = BlockingScheduler()
mode = os.environ.get("MODE","satellite")
logger.info(f"MODE=> {mode}")
is_leader = mode == "leader"
last_run_times = {}

logger.info(f"Collector type: {mode}")

is_synch_photos = os.getenv("SYNCH_PHOTOS", "false").lower() == "true"
logger.info(f"SYNCH_PHOTOS=> {is_synch_photos}")

def shutdown(signum, frame):
    logger.info(f"Received signal {signum}, shutting down scheduler...")
    scheduler.shutdown(wait=False)
    sys.exit(0)

def job_listener(event):
    last_run_times[event.job_id] = event.scheduled_run_time.isoformat()

scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

def toggle_logging_level(signum, frame):
    current_level = logging.root.level
    new_level_name = LOG_LEVEL_MAP.get(current_level, 'DEBUG')
    new_level = getattr(logging, new_level_name.upper(), logging.INFO)

    logging.root.setLevel(new_level)
    logger.setLevel(new_level)
    for handler in logging.root.handlers:
        handler.setLevel(new_level)

    logger.error(f"!!! Logging level dynamically switched to: {new_level_name} !!!")


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


def list_jobs_handler(signum, frame):

    job_list = []
    config = {
        "leader_role": None if not elector else elector.role.name,
        "leader_state": None if not elector else elector.state.name
    }

    config["jobs"] = job_list

    for job in scheduler.get_jobs():
        logger.info(f"Job: {job}")
        logger.info(f"Job next run: {job.next_run_time}")
        if not last_run_times.get(job.id):
            logger.info(f"Job last run: {last_run_times.get(job.id)}")
        logger.info(f"Job trigger: {job.trigger}")
        logger.info(f"Job pending: {job.pending}")
        logger.info(f"Job elector: {elector}")
        if elector is not None:
            logger.info(f"Job leader role: {elector.role}")
            logger.info(f"Job leader state: {elector.state}")
        job_list.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "last_run": last_run_times.get(job.id) if last_run_times.get(job.id) else None,
            "trigger": str(job.trigger),
            "pending": job.pending,
        })
    with open('/tmp/scheduler_config.json', 'w') as f:
        json.dump(config, f)

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGUSR1, log_level_config_manager.toggle_logging_level)
signal.signal(signal.SIGUSR2, list_jobs_handler)

logger.info(f"SIGUSR1 signal registered to toggle logging level. Initial level: {logging.getLevelName(logging.root.level)}")

scheduler.start()


