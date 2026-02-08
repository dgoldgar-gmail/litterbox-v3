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

def post_worker_init(worker):
    from utils import initialize_logger_config
    initialize_logger_config()
