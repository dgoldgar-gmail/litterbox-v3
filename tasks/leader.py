import os
import socket
import threading
import time
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from utils import configure_logging, set_homeassistant_state, get_homeassistant_state, send_homeassistant_notification
from config import LEADER_TTL, LEADER_HEARTBEAT_INTERVAL, LEADER_WATCHDOG_INTERVAL
from apscheduler.schedulers.base import STATE_PAUSED

import logging

logger = logging.getLogger(__name__)
configure_logging()


def leadership_watchdog(elector, scheduler, interval=LEADER_WATCHDOG_INTERVAL):
    previous_state = None
    while True:
        try:
            leader = elector.is_leader()
            if scheduler.running:
                if leader and scheduler.state == STATE_PAUSED:
                    scheduler.resume()
                    if previous_state != True:
                        logger.info("Scheduler resumed (gained leadership)")
                    previous_state = True
                elif not leader and scheduler.state != STATE_PAUSED:
                    scheduler.pause()
                    if previous_state != False:
                        logger.info("Scheduler paused (lost leadership)")
                    previous_state = False
            else:
                previous_state = None
        except Exception:
            logger.exception("Error in leadership watchdog")
        time.sleep(interval)


class LeaderElector:
    def __init__(self, entity_id="sensor.scheduler_leader",
                 heartbeat_interval=LEADER_HEARTBEAT_INTERVAL, ttl=LEADER_TTL):
        self.entity_id = entity_id
        self.heartbeat_interval = heartbeat_interval
        self.ttl = ttl
        self.host = socket.gethostname()
        self.pid = os.getpid()
        self._stop = threading.Event()
        self._thread = None
        self._leader = False  # Track local leadership state
        self._startup_delay = random.uniform(0, 5)  # Reduce startup race

    def start(self):
        self._thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _heartbeat_loop(self):
        # optional startup delay
        time.sleep(self._startup_delay)

        while not self._stop.is_set():
            try:
                # --- Read HA leadership sensor ---
                state = get_homeassistant_state(self.entity_id)
                attrs = state.get("attributes", {}) if state else {}
                last = attrs.get("last_heartbeat")
                last_dt = None

                if last:
                    try:
                        # Parse UTC timestamp
                        last_dt = datetime.fromisoformat(last)
                        if last_dt.tzinfo is None:
                            last_dt = last_dt.replace(tzinfo=ZoneInfo("UTC"))
                    except ValueError:
                        logger.warning("Invalid last_heartbeat format, ignoring")
                        last_dt = None

                current_leader = attrs.get("host") == self.host and attrs.get("pid") == self.pid

                # --- Current UTC time ---
                now_utc = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))

                # Determine if leadership should be acquired
                ttl_expired = (last_dt is None) or (now_utc - last_dt > timedelta(seconds=self.ttl))
                acquire_leadership = ttl_expired or current_leader or last_dt is None

                if acquire_leadership:
                    # Write UTC to HA sensor
                    payload = {
                        "state": "active",
                        "attributes": {
                            "host": self.host,
                            "pid": self.pid,
                            "last_heartbeat": now_utc.isoformat(),
                        },
                    }
                    set_homeassistant_state(self.entity_id, payload)

                    # Only notify on leadership change
                    if not self._leader:
                        local_now = now_utc.astimezone(ZoneInfo("America/New_York"))
                        local_str = local_now.strftime("%Y-%m-%d %H:%M:%S %Z")
                        logger.info("Leadership acquired")
                        send_homeassistant_notification(
                            service="persistent_notification",
                            message=f"{self.host} elected scheduler leader at {local_str}",
                            title="Leadership Acquired",
                        )
                    self._leader = True
                else:
                    if self._leader:
                        logger.info("Leadership lost")
                    self._leader = False

            except Exception:
                if self._leader:
                    logger.warning("Lost leadership due to HA connectivity issue")
                self._leader = False
                logger.exception("Failed to read/write HA leadership sensor")

            time.sleep(self.heartbeat_interval)

    def is_leader(self):
        return self._leader
