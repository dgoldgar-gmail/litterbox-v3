import logging
import signal
import sys
from apscheduler.schedulers.blocking import BlockingScheduler
from tasks.collector import collect_host_info

scheduler = BlockingScheduler()

logger = logging.getLogger(__name__)

# Example schedules
scheduler.add_job(collect_host_info, 'interval', minutes=1)

def shutdown(signum, frame):
    print(f"Received signal {signum}, shutting down scheduler...")
    scheduler.shutdown(wait=False)
    sys.exit(0)

# Catch termination signals
signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

if __name__ == "__main__":
    print("Starting scheduler...")
    scheduler.start()

