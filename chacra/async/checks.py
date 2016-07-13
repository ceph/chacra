from celery.task.control import inspect
from errno import errorcode
from chacra import models
from sqlalchemy.exc import OperationalError
import logging


logger = logging.getLogger(__name__)


class SystemCheckError(Exception):

    def __init__(self, message):
        self.message = message


def celery_has_workers():
    """
    The ``stats()`` call will return different stats/metadata information about
    celery worker(s).  An empty/None result will mean that there aren't any
    celery workers in use.
    """
    stats = inspect().stats()
    if not stats:
        raise SystemCheckError('No running Celery worker was found')


def rabbitmq_is_running():
    """
    If checking for worker stats, an ``IOError`` may be raised depending on the
    problem for the RabbitMQ connection.
    """
    try:
        celery_has_workers()
    except IOError as e:
        msg = "Error connecting to RabbitMQ: " + str(e)
        if len(e.args):
            if errorcode.get(e.args[0]) == 'ECONNREFUSED':
                msg = "RabbitMQ is not running or not reachable"
        raise SystemCheckError(msg)


def database_connection():
    """
    A very simple connection that should succeed if there is a good/correct
    database connection.
    """
    try:
        models.Project.get(1)
    except OperationalError as exc:
        raise SystemCheckError(
            "Could not connect or retrieve information from the database: %s" % exc.message)


system_checks = (
    rabbitmq_is_running,
    celery_has_workers,
    database_connection
)


def is_healthy():
    """
    Perform all the registered system checks and detect if anything fails so
    that the system can send a callback indicating an OK status
    """
    for check in system_checks:
        try:
            check()
        except Exception:
            logger.exception('system is unhealthy')
            return False
    return True
