import os, socket, threading, time, random, logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from enum import Enum, auto

from utils import configure_logging
from home_assistant_client import HomeAssistantClient
from config import Configuration

configuration = Configuration()
home_assistant_client = HomeAssistantClient()
logger = logging.getLogger(__name__)
configure_logging()


class LeadershipRole(Enum):
    LEADER = auto()
    FOLLOWER = auto()

class LeadershipState(Enum):
    ACTIVE = auto()
    STANDBY = auto()

class LeaderElector:
    def __init__(self, scheduler, configuration, entity_id="sensor.scheduler_leader"):
        self.scheduler = scheduler
        self.config = configuration
        self.entity_id = entity_id
        self.ttl = configuration.LEADER_TTL
        self.heartbeat_interval = configuration.LEADER_HEARTBEAT_INTERVAL

        self.state = LeadershipState.STANDBY
        self.role = LeadershipRole.FOLLOWER

        self.host = socket.gethostname()
        self.pid = os.getpid()
        self._stop = threading.Event()
        self._thread = None
        self._startup_delay = random.uniform(0, 5)

    def start(self):
        self._thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._thread.start()
        threading.Thread(
            target=self.leadership_watchdog,
            daemon=True
        ).start()

    def stop(self):
        self._stop.set()

    def promote_to_active(self):
        logger.info(f"--- PROMOTING {self.host} TO ACTIVE ---")
        from tasks.collector import collect_application_info, collect_certificate_info
        from tasks.duck_dns import update_dns_info

        self.scheduler.add_job(
            collect_application_info, 'interval',
            minutes=self.config.COLLECT_APP_INFO_INTERVAL,
            id="app_info",
            replace_existing=True,
            next_run_time=datetime.now()
        )
        self.scheduler.add_job(
            update_dns_info, 'cron',
            minute=0, hour=f'*/{self.config.UPDATE_DUCK_DNS_INTERVAL}',
            id="duckdns_update",
            replace_existing=True
        )
        self.scheduler.add_job(
            collect_certificate_info, 'cron',
            minute=0, hour=f'*/{self.config.COLLECT_CERTIFICATE_INFO_INTERVAL}',
            id="certificate_inf",
            replace_existing=True
        )
        self.state = LeadershipState.ACTIVE

    def demote_to_standby(self):
        logger.info(f"--- DEMOTING {self.host} TO STANDBY ---")
        for job_id in ["app_info", "duckdns_update", "certificate_inf"]:
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
        self.state = LeadershipState.STANDBY

    def _heartbeat_loop(self):
        time.sleep(self._startup_delay)
        while not self._stop.is_set():
            try:
                state_data = home_assistant_client.get_homeassistant_state(self.entity_id)
                attrs = state_data.get("attributes", {}) if state_data else {}
                last = attrs.get("last_heartbeat")

                # Logic to check if current leader is valid
                last_dt = datetime.fromisoformat(last).replace(tzinfo=ZoneInfo("UTC")) if last else None
                now_utc = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))

                is_currently_me = (attrs.get("host") == self.host and attrs.get("pid") == self.pid)
                is_expired = (last_dt is None or (now_utc - last_dt > timedelta(seconds=self.ttl)))

                if is_currently_me or is_expired:
                    # We are taking/keeping leadership
                    payload = {
                        "state": "active",
                        "attributes": {
                            "host": self.host, "pid": self.pid,
                            "last_heartbeat": now_utc.isoformat(),
                            "status": self.state.name
                        }
                    }
                    home_assistant_client.set_homeassistant_state(self.entity_id, payload)

                    if self.role == LeadershipRole.FOLLOWER:
                        logger.info("Leadership Acquired via Heartbeat")
                    self.role = LeadershipRole.LEADER
                else:
                    if self.role == LeadershipRole.FOLLOWER:
                        logger.info("Leadership Surrendered (Another node is active)")
                    self.role = LeadershipRole.FOLLOWER

            except Exception:
                logger.exception("Heartbeat failure")
                self.role = LeadershipRole.FOLLOWER

            time.sleep(self.heartbeat_interval)

    def leadership_watchdog(self):
        """Monitors the election result and syncs the scheduler jobs."""
        is_active_locally = False
        while True:
            try:
                should_be_active = self.role == LeadershipRole.LEADER
                if self.role == LeadershipRole.LEADER and self.state == LeadershipState.STANDBY:
                    self.promote_to_active()
                elif self.role == LeadershipRole.FOLLOWER and self.state == LeadershipState.ACTIVE:
                    self.demote_to_standby()
            except Exception:
                logger.exception("Error in leadership watchdog")
            time.sleep(configuration.LEADER_WATCHDOG_INTERVAL)