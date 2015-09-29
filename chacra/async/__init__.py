import pecan
from celery import Celery
from datetime import timedelta
import requests
import jenkins
import json
import os
import logging
logger = logging.getLogger(__name__)


def get_pecan_config():
    try:
        os.environ['PECAN_CONFIG']
    except KeyError:
        here = os.path.abspath(os.path.dirname(__file__))
        config_path = os.path.abspath(os.path.join(here, '../config/config.py'))
        return config_path


pecan.configuration.set_config(get_pecan_config(), overwrite=True)
# FIXME: this needs to be configurable. Also, not sure if this is the right way
# to configure Celery for multiple tasks running in a single service.
# TODO: Investigate if this could be `chacra.async.rpm` and
# `chacra.async.debian` or if it doesn't matter
app = Celery('chacra.async', broker='amqp://guest@localhost//')

app.conf.update(
    CELERYBEAT_SCHEDULE={
        'check-idle-every-30-seconds': {
            'task': 'async.check_idling',
            # FIXME: no way we want this to be 10 seconds
            'schedule': timedelta(seconds=10),
        },
        'add-every-30-seconds': {
            'task': 'async.check_queue',
            # FIXME: no way we want this to be 10 seconds
            'schedule': timedelta(seconds=10),
        },
    },
    nodes=pecan.conf.nodes,
    pecan_app=pecan.conf.server,
    jenkins=pecan.conf.jenkins
)
