from datetime import timedelta
import os
import pecan
import socket
import logging
import warnings

from celery import Celery
from celery.signals import worker_init
from chacra import models

from pecan.configuration import Config

try:
    from logging.config import dictConfig as load_logging_config
except ImportError:
    from logutils.dictconfig import dictConfig as load_logging_config  # noqa


logger = logging.getLogger(__name__)


def configure_celery_logging():
    logging = pecan.conf.get('logging', {})
    debug = pecan.conf.get('debug', False)
    if logging:
        if debug:
            try:
                #
                # By default, Python 2.7+ silences DeprecationWarnings.
                # However, if conf.app.debug is True, we should probably ensure
                # that users see these types of warnings.
                #
                from logging import captureWarnings
                captureWarnings(True)
                warnings.simplefilter("default", DeprecationWarning)
            except ImportError:
                # No captureWarnings on Python 2.6, DeprecationWarnings are on
                pass

        if isinstance(logging, Config):
            logging = logging.to_dict()
        if 'version' not in logging:
            logging['version'] = 1
        load_logging_config(logging)


@worker_init.connect
def bootstrap_pecan(signal, sender):
    try:
        config_path = os.environ['PECAN_CONFIG']
    except KeyError:
        here = os.path.abspath(os.path.dirname(__file__))
        # XXX this will not hold true when installing as a binary
        config_path = os.path.abspath(os.path.join(here, '../config/config.py'))

    pecan.configuration.set_config(config_path, overwrite=True)
    configure_celery_logging()
    # Once configuration is set we need to initialize the models so that we can connect
    # to the DB wth a configured mapper.
    models.init_model()


app = Celery(
    'chacra.async',
    broker='amqp://guest@localhost//',
    include=['chacra.async.rpm', 'chacra.async.debian', 'chacra.async.recurring']
)


try:
    seconds = pecan.conf.polling_cycle
except AttributeError:
    bootstrap_pecan(None, None)
    seconds = pecan.conf.polling_cycle

app.conf.update(
    CELERYBEAT_SCHEDULE={
        'poll-repos': {
            'task': 'chacra.async.recurring.poll_repos',
            'schedule': timedelta(
                seconds=seconds),
            'options': {'queue': 'poll_repos'}
        },
    },
)


# helpers
#
#
def post_status(state, json):
    """
    Nicer interface to send a status report on repo creation if configured.

    :param state: Any useful (single-word) string to describe the current
                  status of a repo. Like: 'queued', 'building', 'ready', 'requested'
    :param json: The actual ``json`` representing the Repo model object (or any subset of it)
    :param project_name: The name of the project the repository belongs to
    """
    if not getattr(pecan.conf, 'callback_url', False):
        return
    from chacra.async import recurring
    json['state'] = state
    project_name = json['project_name']
    recurring.callback.apply_async(
        args=(json, project_name),
    )


def post_requested(repo):
    json = repo.__json__()
    post_status('requested', json)


def post_queued(repo):
    json = repo.__json__()
    post_status('queued', json)


def post_building(repo):
    json = repo.__json__()
    post_status('building', json)


def post_ready(repo):
    json = repo.__json__()
    post_status('ready', json)


def post_if_healthy():
    """
    If system is healthy, make an asynchronous request to a configured remote
    system. Requires the following in the config file::

        health_ping = True
        health_ping_url = "https://check.example.com"

    """
    health_ping = getattr(pecan.conf, 'health_ping', False)
    health_ping_url = getattr(pecan.conf, 'health_ping_url', False)

    if not health_ping or not health_ping_url:
        logger.info("System is not configured to send health ping.")
        return

    from chacra.async import recurring, checks

    if not checks.is_healthy():
        logger.error("System is not healthy and will not send health ping.")
        return

    hostname = socket.gethostname()
    url = os.path.join(health_ping_url, hostname, '')
    logger.info("Posting health ping to: %s", url)
    recurring.callback.apply_async(
        args=({}, None),
        kwargs=dict(url=url),
    )
