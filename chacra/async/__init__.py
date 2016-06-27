from datetime import timedelta
import os
import pecan

from celery import Celery
from celery.signals import worker_init
from chacra import models


@worker_init.connect
def bootstrap_pecan(signal, sender):
    try:
        config_path = os.environ['PECAN_CONFIG']
    except KeyError:
        here = os.path.abspath(os.path.dirname(__file__))
        # XXX this will not hold true when installing as a binary
        config_path = os.path.abspath(os.path.join(here, '../config/config.py'))

    pecan.configuration.set_config(config_path, overwrite=True)
    # Once configuration is set we need to initialize the models so that we can connect
    # to the DB wth a configured mapper.
    models.init_model()


app = Celery(
    'chacra.async',
    broker='amqp://guest@localhost//',
    include=['chacra.async.rpm', 'chacra.async.deb', 'chacra.async.recurring']
)


app.conf.update(
    CELERYBEAT_SCHEDULE={
        'poll-repos': {
            'task': 'async.recurring.poll_repos',
            'schedule': timedelta(
                seconds=pecan.conf.polling_cycle),
            'options': {'queue': 'poll_repos'}
        },
    },
)
