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
def bootstrap_pecan(signal, sender, **kw):
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
    'chacra.asynch',
    broker='amqp://guest@localhost//',
    include=['chacra.asynch.rpm', 'chacra.asynch.debian', 'chacra.asynch.recurring']
)


try:
    seconds = pecan.conf.polling_cycle
except AttributeError:
    bootstrap_pecan(None, None)
    seconds = pecan.conf.polling_cycle

app.conf.update(
    CELERYBEAT_SCHEDULE={
        'poll-repos': {
            'task': 'chacra.asynch.recurring.poll_repos',
            'schedule': timedelta(seconds=seconds),
            'options': {'queue': 'poll_repos'}
        },
        'purge-repos': {
            'task': 'chacra.asynch.recurring.purge_repos',
            'schedule': timedelta(days=1),
        },
    },
)


# helpers
#
#
def post_status(status, repo_obj, _callback=None):
    """
    Nicer interface to send a status report on repo creation if configured.

    :param state: Any useful (single-word) string to describe the current
                  status of a repo. Like: 'queued', 'building', 'ready', 'requested'
    :param json: The actual ``json`` representing the Repo model object (or any subset of it)
    :param project_name: The name of the project the repository belongs to
    """
    if not getattr(pecan.conf, 'callback_url', False):
        return
    from chacra.asynch import recurring
    # this needs a better implementation
    hostname = getattr(pecan.conf, 'hostname', socket.gethostname())
    host_url = 'https://%s/' % hostname
    api_url = os.path.join(host_url, 'repos', '')
    repos_url = os.path.join(host_url, 'r', '')
    callback = _callback or recurring.callback.apply_async
    repo_obj_dict = repo_obj.__json__()
    repo_obj_dict['status'] = status
    repo_obj_dict['chacra_url'] = os.path.join(api_url, repo_obj.uri, '')
    repo_obj_dict['url'] = os.path.join(repos_url, repo_obj.uri, '')
    project_name = repo_obj_dict['project_name']

    # Some fields from the object may not be JSON serializable by `requests`
    # (like datetime objects) so we rely on Pecan to deal with those and encode
    # them for us
    data = pecan.jsonify.encode(repo_obj_dict)
    callback(
        args=(data, project_name),
    )


def post_requested(repo):
    post_status('requested', repo)


def post_queued(repo):
    post_status('queued', repo)


def post_building(repo):
    post_status('building', repo)


def post_ready(repo):
    post_status('ready', repo)


def post_deleted(repo):
    post_status('deleted', repo)


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

    from chacra.asynch import recurring, checks

    if not checks.is_healthy():
        logger.error("System is not healthy and will not send health ping.")
        return

    hostname = getattr(pecan.conf, 'hostname', socket.gethostname())
    url = os.path.join(health_ping_url, hostname, '')
    logger.info("Posting health ping to: %s", url)
    recurring.callback.apply_async(
        args=({}, None),
        kwargs=dict(url=url),
    )
