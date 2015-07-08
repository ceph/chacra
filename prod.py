from pecan.hooks import TransactionHook, RequestViewerHook
from chacra.hooks.cors import CorsHook
from chacra import models


# Server Specific Configurations
server = {
    'port': '8000',
    'host': '0.0.0.0'
}

# Pecan Application Configurations
app = {
    'root': 'chacra.controllers.root.RootController',
    'modules': ['chacra'],
    'default_renderer': 'json',
    'hooks': [
        TransactionHook(
            models.start,
            models.start_read_only,
            models.commit,
            models.rollback,
            models.clear
        ),
        CorsHook(),
    ],
    'debug': True,
}

logging = {
    'loggers': {
        'root': {'level': 'INFO', 'handlers': ['console']},
        'chacra': {'level': 'DEBUG', 'handlers': ['console']},
        'pecan.commands.serve': {'level': 'DEBUG', 'handlers': ['console']},
        'py.warnings': {'handlers': ['console']},
        '__force_dict__': True
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'color'
        }
    },
    'formatters': {
        'simple': {
            'format': ('%(asctime)s %(levelname)-5.5s [%(name)s]'
                       '[%(threadName)s] %(message)s')
        },
        'color': {
            '()': 'pecan.log.ColorFormatter',
            'format': ('%(asctime)s [%(padded_color_levelname)s] [%(name)s]'
                       '[%(threadName)s] %(message)s'),
            '__force_dict__': True
        }
    }
}

sqlalchemy = {
    'url': 'sqlite:///dev.db',
    #'url': 'postgresql+psycopg2://USER:PASSWORD@DB_HOST/DB_NAME',
    'echo':          True,
    'echo_pool':     True,
    'pool_recycle':  3600,
    'encoding':      'utf-8'
}

# location for storing uploaded binaries
binary_root = '%(confdir)s/public'

# When True it will set the headers so that Nginx can serve the download
# instead of Pecan.
delegate_downloads = False
