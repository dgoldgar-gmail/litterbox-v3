# gunicorn.conf.py

bind = "0.0.0.0:5555"
workers = 4
loglevel = "info"
errorlog = "-" 
accesslog = "-"
worker_class = "gevent"
timeout = 300

logconfig_dict = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] [%(levelname)s] [%(name)s] :: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        }
    },
    'loggers': {
        '': {  # This is the root logger
            'level': loglevel.upper(),
            'handlers': ['console'],
            'propagate': True,
        }
    }
}

"""
def post_worker_init(worker):
    from log_level_config_manager import LogLevelConfigManager
    log_level_config_manager = LogLevelConfigManager()
    log_level_config_manager.initialize_logger_config()

def on_starting(server):
    import socket
    from home_assistant_client import HomeAssistantClient
    home_assistant_client = HomeAssistantClient()
    host_name = socket.gethostname()
    title = f"Litterbox Restarted on {host_name}"
    message = "Litterbox restarted successfully"
    home_assistant_client.send_homeassistant_notification("persistent_notification", message="Litterbox restarted", title=title)
"""