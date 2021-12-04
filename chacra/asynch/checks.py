import logging
import os
import subprocess

from celery.app.control import Inspect
from errno import errorcode
from pecan import conf
from chacra import models
from sqlalchemy.exc import OperationalError


logger = logging.getLogger(__name__)


class SystemCheckError(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


def celery_has_workers():
    """
    The ``stats()`` call will return different stats/metadata information about
    celery worker(s).  An empty/None result will mean that there aren't any
    celery workers in use.
    """
    stats = Inspect().stats()
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


def disk_has_space(_popen=None):
    """
    If the disk where repos/binaries doesn't have enough space, fail the health
    check to prevent failing when the binaries are getting posted
    """
    popen = _popen or subprocess.Popen
    command = ['df', conf.get('repo_path', '/')]
    result = popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if result.returncode > 0:
        raise SystemCheckError("failed disk check: %s" % result.stderr.read())
    out = result.communicate()[0]
    device, size, used, available, percent, mountpoint = out.split('\n')[1].split()
    if int(percent.strip().split('%')[0]) > 85:
        msg = 'disk %s almost full. Used: %s' % (device, percent)
        raise SystemCheckError(msg)


def fail_health_check():
    """
    Checks for the existance of a file and if that file exists it fails
    the check. This is used to manually take a node out of rotation for
    maintenance.
    """
    check_file_path = getattr(conf, "fail_check_trigger_path", "/tmp/fail_check")
    if os.path.exists(check_file_path):
        raise SystemCheckError("%s was found, failing health check" % check_file_path)


system_checks = (
    rabbitmq_is_running,
    celery_has_workers,
    database_connection,
    fail_health_check,
    disk_has_space,
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
