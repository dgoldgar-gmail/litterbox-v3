
import datetime
import json
import logging
import os
import shutil
import yaml

from yaml import SafeLoader, SafeDumper

logger = logging.getLogger(__name__)

class Configuration:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Configuration, cls).__new__(cls)
            # This flag is attached only to the singleton instance
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # Stop everything if we've already set up this process
        if self._initialized:
            return

        self.config = {}
        self.UNKNOWN = "UNKNOWN"
        self.REGISTRY = "192.168.50.15:5000"

        self.SSH_USER = os.environ.get("SSH_USER", "root")

        # Home Assistant
        self.HOME_ASSISTANT_API_URL = "https://192.168.50.14:8123/api"
        self.KEY_FILE = os.environ.get("KEY_FILE", "/root/.ssh/homeassistant")

        # Directories
        self.BACKUP_DIR = self.__setup_directory_environment("BACKUP_DIR", "/app/backups")
        self.CONFIG_DIR = self.__setup_directory_environment("CONFIG_DIR", "app/config")
        self.JINJA_TEMPLATES = self.__setup_directory_environment("JINJA_TEMPLATES", "app/templates")
        self.GENERATED = self.__setup_directory_environment("GENERATED", "app/generated")
        self.GIT_REPO_PATH = self.__setup_directory_environment("GIT_REPO_PATH", "/app/git")
        self.PHOTOPRISM_PATH = self.__setup_directory_environment("PHOTOPRISM_PATH", "/app/photoprism")

        # Files
        self.SECRETS_YAML = self.__load_config_file("SECRETS_YAML", "secrets.yaml")
        self.OVERVIEW_MAPPING = self.__load_config_file("OVERVIEW_MAPPING", "overview_mapping.yaml")
        self.UNIFIED_MAPPING = self.__load_config_file("UNIFIED_MAPPING", "unified_mapping.yaml")
        self.APPLICATIONS_CONFIG = self.__load_config_file("APPLICATIONS_CONFIG", "applications.json")
        self.LOGGER_CONFIG = self.__load_config_file("LOGGER_CONFIG", "logger_config.json")
        self.ICLOUD_PHOTOS_LOCK = self.__load_config_file("ICLOUD_PHOTOS_LOCK", f"{self.PHOTOPRISM_PATH}/icloud_sessions/icloud_photos_lock.json", True)

        self.UNIFIED_MAPPING_SCHEMA = self.__load_config_file("UNIFIED_MAPPING_SCHEMA", "unified_mapping_schema.json")
        self.OVERVIEW_MAPPING_SCHEMA = self.__load_config_file("OVERVIEW_MAPPING_SCHEMA", "overview_mapping_schema.json")
        self.APPLICATIONS_CONFIG_SCHEMA = self.__load_config_file("APPLICATIONS_CONFIG_SCHEMA", "applications_schema.json")
        self.ANSIBLE_INVENTORY_SCHEMA = self.__load_config_file("ANSIBLE_INVENTORY_SCHEMA", "ansible_inventory_schema.json")
        self.ANSIBLE_SITE_SCHEMA = self.__load_config_file("ANSIBLE_SITE_SCHEMA", "ansible_site_schema.json")

        self.ANSIBLE_VAULT_PASS_PATH = os.environ.get("ANSIBLE_VAULT_PASS_PATH", "/app/.ansible/vault_pass")
        self.ANSIBLE_INVENTORY = self.__load_config_file("ANSIBLE_CONFIG", "ansible/inventory/hosts.yml", True)
        self.ANSIBLE_SITE = self.__load_config_file("ANSIBLE_SITE", "ansible/project/site.yml", True)

        # Scheduler Configuration
        self.COLLECT_APP_INFO_INTERVAL = int(os.environ.get("COLLECT_APP_INFO_INTERVAL", 5))
        self.COLLECT_HOST_INFO_INTERVAL = int(os.environ.get("COLLECT_HOST_INFO_INTERVAL", 5))
        self.COLLECT_CERTIFICATE_INFO_INTERVAL = int(os.environ.get("COLLECT_CERTIFICATE_INFO_INTERVAL", 12))
        self.UPDATE_DUCK_DNS_INTERVAL = int(os.environ.get("UPDATE_DUCK_DNS_INTERVAL", 12))
        self.SYNCH_PHOTOS_INTERVAL = int(os.environ.get("SYNCH_PHOTOS_INTERVAL", 7))

        self.LEADER_TTL = int(os.environ.get("LEADER_TTL", 240))
        self.LEADER_WATCHDOG_INTERVAL = int(os.environ.get("LEADER_TTL", 60))
        self.LEADER_HEARTBEAT_INTERVAL = int(os.environ.get("LEADER_TTL", 60))

        # Seal the instance
        self._initialized = True
        logger.info("Configuration initialized successfully.")

    def __setup_directory_environment(self, name, default):
        value = os.environ.get(name)
        if value is None:
            if default is None:
                raise ValueError(f"Environment variable {name} is required!")
            else:
                value = default
        logger.info(f"{name} set to: {value}")
        return value

    # I think this is named wrong....
    def __load_config_file(self, variable_name, file_name, full_path=False):
        if full_path:
            config_file = f"{file_name}"
        else:
            config_file = f"{self.CONFIG_DIR}/{file_name}"
        logger.info(f"{variable_name} set to: {config_file}")
        return config_file

    def get_all_hosts(self):
        mapping_data = self.load_yaml_data(self.UNIFIED_MAPPING)
        hosts = mapping_data['hosts']
        return  [item['name'] for item in hosts]


    def load_yaml_data(self, yaml_file_path):
        """Loads YAML data from the specified file."""
        logger.info(f"Loading YAML data from {yaml_file_path}")
        if os.path.exists(yaml_file_path):
            try:
                with open(yaml_file_path, 'r') as f:
                    content = f.read()
                    if content:
                        loaded_data = yaml.load(content, Loader=SafeLoader)
                        logger.debug(f"Data loaded successfully from {yaml_file_path}.")
                        return loaded_data if loaded_data is not None else {}
                    else:
                        logger.info(f"File {yaml_file_path} is empty. Initializing with empty data.")
                        return {}
            except yaml.YAMLError as e:
                logger.info(f"Error parsing YAML from {yaml_file_path}: {e}")
                return {}
            except Exception as e:
                logger.info(f"An unexpected error occurred loading YAML from {yaml_file_path}: {e}")
                return {}
        logger.info(f"File {yaml_file_path} not found. Initializing with empty data.")
        return {}

    def save_yaml_data(self, app_data_dict, yaml_file_path):
        self.create_backup(yaml_file_path)  # Same backup logic
        try:
            with open(yaml_file_path, 'w') as f:
                yaml.safe_dump(app_data_dict, f, sort_keys=False)
                logger.info(f"YAML data saved successfully to {yaml_file_path}")
        except Exception as e:
            logger.info(f"Error saving YAML data to {yaml_file_path}: {e}")

    # --- JSON Helper Functions ---

    def load_json_data(self, json_file_path):
        with open(json_file_path, 'r') as f:
            content = f.read()
            return json.loads(content)

    def save_json_data(self, app_data_dict, json_file_path, backup=True):
        if backup:
            self.create_backup(json_file_path)

        try:
            with open(json_file_path, 'w') as f:
                json.dump(app_data_dict, f, indent=2)
                logger.info(f"Data saved successfully to {json_file_path}. Saved {len(app_data_dict)} applications.")
        except Exception as e:
            logger.info(f"Error saving data to {json_file_path}: {e}")

    def create_backup(self, file_path):
        if os.path.exists(file_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_dir = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            backup_dir = os.path.join(file_dir, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            backup_file_path = os.path.join(backup_dir, f"{file_name.replace('.', f'_{timestamp}.', 1)}")

            try:
                shutil.copyfile(file_path, backup_file_path)
                logger.info(f"Backup created: {backup_file_path}")
            except Exception as e:
                logger.info(f"Error creating backup of {file_path}: {e}")
