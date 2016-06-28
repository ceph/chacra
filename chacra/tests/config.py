from pecan.hooks import TransactionHook
from chacra import models


# Server Specific Configurations
server = {
    'port': '8080',
    'host': '0.0.0.0'
}

# Pecan Application Configurations
app = {
    'root': 'chacra.controllers.root.RootController',
    'modules': ['chacra'],
    'static_root': '%(confdir)s/public',
#    'default_renderer': 'json',
    'guess_content_type_from_ext': False,
    'hooks': [
        TransactionHook(
            models.start,
            models.start_read_only,
            models.commit,
            models.rollback,
            models.clear
        ),
    ],
    'debug': True,
    #'errors': {
    #    404: '/error/404',
    #    '__force_dict__': True
    #}
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
    # You may use SQLite for testing
    'url': 'sqlite:///dev.db',
    # When you set up PostreSQL, it will look more like:
    #'url': 'postgresql+psycopg2://USER:PASSWORD@DB_HOST/DB_NAME',
    'echo':          True,
    'echo_pool':     True,
    'pool_recycle':  3600,
    'encoding':      'utf-8'
}

binary_root = '/tmp/'
distributions_root = '/tmp/'

# When True it will set the headers so that Nginx can serve the download
# instead of Pecan.
delegate_downloads = False

api_user = 'admin'
api_key = 'secret'

polling_cycle = 30

# Use this to define how distributions files will be created per project
distributions = {
    "defaults": {
        "DebIndices": "Packages Release . .gz .bz2",
        "DscIndices": "Sources Release .gz .bz2",
        "Contents": ".gz .bz2",
        "Origin": "RedHat",
        "Description": "",
        "Architectures": "amd64 armhf i386 source",
        "Suite": "stable",
        "Components": "main",
    },
    "ceph": {
        "Description": "Ceph distributed file system",
    },
}
