import logging
from config import Configuration

LOG_LEVEL_MAP = {
    logging.INFO: 'DEBUG',
    logging.DEBUG: 'INFO'
}

configuration = Configuration()
logger = logging.getLogger(__name__)

class LogLevelConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

    def configure_logging(
        level=logging.INFO,
        *,
        silence_libs=True,
        force=False,
    ):
        root = logging.getLogger()
        if root.handlers and not force:
            root.setLevel(level)
            return
        root.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        handler.setFormatter(formatter)
        root.handlers.clear()
        root.addHandler(handler)

        if silence_libs:
            logging.getLogger("paramiko.transport").setLevel(logging.WARNING)
            logging.getLogger("apscheduler").setLevel(logging.INFO)
            logging.getLogger("urllib3").setLevel(logging.WARNING)

    def get_all_loggers(self):
        logging.getLogger('werkzeug')
        loggers = [logging.getLogger()]
        loggers += [logging.getLogger(name) for name in logging.root.manager.loggerDict]

        all_loggers = []

        for logger in sorted(loggers, key=lambda x: x.name):
            next_logger = {}

            name = logger.name if logger.name != 'root' else 'root'
            level = logging.getLevelName(logger.level)
            eff_level = logging.getLevelName(logger.getEffectiveLevel())

            next_logger['name'] = name
            next_logger['level'] = level
            next_logger['eff_level'] = eff_level

            all_loggers.append(next_logger)
        return all_loggers

    def apply_logger_config(self, data):
        for entry in data:
                name = entry.get('name')
                level = entry.get('level')
                if name and level:
                    the_logger = logging.getLogger(name)
                    the_logger.setLevel(level.upper())
                    the_logger.propagate = True
                    logger.info(f"Set logger {name} to {level}")

    def initialize_logger_config(self):
        logger_config = configuration.load_yaml_data(configuration.LOGGER_CONFIG)
        self.apply_logger_config(logger_config)


    def toggle_logging_level(self, signum, frame):
        current_level = logging.root.level
        new_level_name = LOG_LEVEL_MAP.get(current_level, 'DEBUG')
        new_level = getattr(logging, new_level_name.upper(), logging.INFO)

        logging.root.setLevel(new_level)
        logger.setLevel(new_level)
        for handler in logging.root.handlers:
            handler.setLevel(new_level)

        logger.error(f"!!! Logging level dynamically switched to: {new_level_name} !!!")
