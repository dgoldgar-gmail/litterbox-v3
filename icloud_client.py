import logging
import os
import piexif

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from pyicloud import PyiCloudService

from config import Configuration
from utils import configure_logging, get_secret, get_timestamp

configuration = Configuration()
logger = logging.getLogger(__name__)
configure_logging()

class LockStatus(str, Enum):
    LOCKED = "locked"
    READY = "ready"
    AWAITING_MFA = "awaiting_2fa"

class ICloudClient:
    def __init__(self, username: str, password: str, session_dir: str):
        self.username = username
        self.password = password
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.api: Optional[PyiCloudService] = None

    def login(self, code=None):
        """Log in. If 'code' is provided, attempt to validate it."""
        self.api = PyiCloudService(
            self.username,
            password=self.password,
            cookie_directory=str(self.session_dir),
        )

        if self.api.requires_2fa and code:
            if not self.api.validate_2fa_code(code):
                raise RuntimeError("MFA validation failed.")
            if not self.api.is_trusted_session:
                self.api.trust_session()
        return self.api

    def is_authorized(self) -> bool:
        """Lightweight check to see if we have a valid session."""
        if not self.api:
            return False
        try:
            # If it doesn't require MFA, we are authorized for the sync
            return self.api.requires_2fa is False
        except Exception as e:
            logger.error(f"Error while trying to check authorization: {e}")
            return False

    def handle_2fa(self):
        """CLI-only: Captures code from terminal."""
        logger.info("Two-factor authentication required.")
        code = input("Enter MFA code: ")
        if not self.api.validate_2fa_code(code):
            raise RuntimeError("MFA validation failed.")
        if not self.api.is_trusted_session:
            logger.info("Trusting session...")
            self.api.trust_session()

    def sync_photos(self, target_root: str, set_exif: bool = False):
        if not self.is_authorized():
            raise RuntimeError("Not authorized. Cannot sync.")

        photos = self.api.photos.all
        logger.info(f"Found {len(photos)} items in iCloud.")



        for photo in photos:
            created = photo.created
            if not created or (Path(target_root) / created.strftime("%Y-%m") / photo.filename).exists():
                continue

            target_dir = Path(target_root) / created.strftime("%Y-%m")
            target_dir.mkdir(parents=True, exist_ok=True)
            filepath = target_dir / photo.filename

            logger.info(f"Downloading: {filepath}")
            download = photo.download()
            with open(filepath, "wb") as f:
                f.write(download.raw.read() if hasattr(download, "raw") else download)

            if set_exif:
                self._set_exif_datetime(filepath, created)

    def _set_exif_datetime(self, filepath: Path, dt: datetime):
        try:
            exif_dict = piexif.load(str(filepath))
            dt_string = dt.strftime("%Y:%m:%d %H:%M:%S")
            exif_dict["0th"][piexif.ImageIFD.DateTime] = dt_string.encode()
            exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = dt_string.encode()
            piexif.insert(piexif.dump(exif_dict), str(filepath))
        except Exception as e:
            logger.error(f"EXIF update failed for {filepath}: {e}")

class ICloudClientLockManager:
    def __init__(self):
        self.sessions_path = f"{configuration.PHOTOPRISM_PATH}/icloud_sessions"
        self.lock_file_path = f"{configuration.ICLOUD_PHOTOS_LOCK}"

        # Ensure the base directory exists
        Path(self.lock_file_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            logger.info(f"Loading lock file: {self.lock_file_path}")
            self.locks = configuration.load_json_data(self.lock_file_path)
            if self.locks is None:
                logger.info("Lock file not found. Creating new dictionary.")
                self.locks = {}
        except Exception as e:
            logger.error(f"Error loading lock file, creating new: {e}")
            self.locks = {}

        # Ensure the file exists on disk immediately
        self._persist()

    def reload(self):
        """Refreshes the internal locks dict from the disk file."""
        self.locks = configuration.load_json_data(self.lock_file_path) or {}

    def _persist(self):
        """Helper to save to disk with error handling."""
        try:
            configuration.save_json_data(self.locks, self.lock_file_path, False)
        except Exception as e:
            logger.error(f"Disk Write Error: Failed to save lock file: {e}")

    def _ensure_user_entry(self, user):
        """Internal check to ensure the user dictionary and keys exist."""
        if user not in self.locks or not isinstance(self.locks[user], dict):
            logger.info(f"Initializing missing or invalid entry for {user}")
            self.locks[user] = {
                'status': "locked",
                'created': get_timestamp(),
                'updated': get_timestamp(),
                'reason': "Initial entry creation"
            }
            self._persist()

        # Guard against existing entries missing specific sub-keys
        if 'status' not in self.locks[user]:
            self.locks[user]['status'] = "locked"
        if 'updated' not in self.locks[user]:
            self.locks[user]['updated'] = get_timestamp()

    def is_locked(self, user):
        """Returns True if the user is NOT explicitly set to 'ready'."""
        try:
            self._ensure_user_entry(user)
            current_status = self.locks[user].get('status')

            logger.info(f"Checking status for {user}: {current_status}")

            # Strictest check: Anything other than 'ready' is a lock.
            if current_status == "ready":
                return False
            return True
        except Exception as e:
            logger.error(f"is_locked check failed for {user}, defaulting to LOCKED: {e}")
            return True

    def update_status(self, user, status: LockStatus, reason=None):

        self.reload()

        old_status = self.locks.get(user, {}).get('status')

        self._ensure_user_entry(user)

        # Since it's a str-Enum, it saves as "awaiting_2fa" automatically
        self.locks[user]['status'] = status
        self.locks[user]['updated'] = get_timestamp()

        if reason:
            self.locks[user]['reason'] = reason

        logger.info(f"Updating {user} status to {status.value}")
        self._persist()

        if old_status == LockStatus.READY and status != LockStatus.READY:
                logger.warning(f"CRITICAL: {user} moved from READY to {status}. Notifying HA.")

                home_assistant_client.send_homeassistant_notification(
                            service="persistent_notification",
                            message=f"Account entered {status} state. Reason: {reason or 'Unknown'}",
                            title=f"iCloud Sync Stopped: {user}"
                        )

    def authenticate_user(self, user, mfa_code=None):
        """
        The Controller: Fetches secrets, invokes client, and manages state.
        """
        try:
            username = get_secret(f"{user}_appleid_username")
            password = get_secret(f"{user}_appleid_password")

            if not username or not password:
                self.update_status(user, "locked", "Missing credentials in secrets.")
                return "FAILED_CREDENTIALS", None

            session_path = f"{self.sessions_path}/{user}"
            client = ICloudClient(username, password, session_path)

            # Step 1: Attempt Login
            api = client.login(code=mfa_code)

            # Step 2: Evaluate State
            if api.requires_2fa:
                self.update_status(user, LockStatus.AWAITING_MFA, "MFA code requested from Apple.")
                return "NEEDS_MFA", client

            if client.is_authorized():
                self.update_status(user, LockStatus.READY, "Session verified and authorized.")
                return "READY", client

            self.update_status(user, LockStatus.LOCKED, "Login completed but authorization failed.")
            return "FAILED_AUTH", client


        except Exception as e:
            error_msg = f"Exception during auth: {str(e)}"
            logger.error(error_msg)
            self.update_status(user, LockStatus.LOCKED, error_msg)
            return "ERROR", None

# -------------------------
# Workflows
# -------------------------

def synch_photos_for_user(user):
    manager = ICloudClientLockManager()

    # Use the Enum for the check
    if manager.is_locked(user):
        logger.error(f"User {user} is locked or awaiting MFA. Skipping sync.")
        return

    status, client = manager.authenticate_user(user)

    if status == LockStatus.READY:
        photo_path = f"{configuration.PHOTOPRISM_PATH}/originals/{user}s_iphone"
        logger.info(f"Syncing photos for {user} to {photo_path}")
        #TODO:  Enable...
        #client.sync_photos(photo_path, set_exif=True)
    else:
        # status will be LockStatus.AWAITING_2FA or LockStatus.LOCKED
        logger.error(f"Sync failed for {user}: Account moved to {status.value}")

def test_login(user):
    """Simulates Step 1: Requesting the code (Process A)"""
    manager = ICloudClientLockManager()
    logger.info(f"--- Step 1: Initializing Login for {user} ---")
    status, _ = manager.authenticate_user(user)
    logger.info(f"Result: {status}")

def test_2fa(user):
    """Simulates Step 2: Providing the code (Process B)"""
    manager = ICloudClientLockManager()
    logger.info(f"--- Step 2: Completing MFA for {user} ---")
    # In a UI, '2fa_code' would come from an API request.
    # Here, we let the client's handle_2fa take over for the CLI test.
    status, client = manager.authenticate_user(user)

    if status == "NEEDS_MFA":
        client.handle_2fa()
        # After handle_2fa, we re-verify to update the lock file
        if client.is_authorized():
            manager.update_status(user, LockStatus.READY, "MFA completed successfully.")
            logger.info("SUCCESS: Lock updated to READY.")

#if __name__ == "__main__":
#    # To test the full cycle, run test_login, wait for the SMS, then run test_2fa.
#    test_login("dave")
#    test_2fa("dave")