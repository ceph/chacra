import pecan
from celery import Celery
import celery
from datetime import timedelta
from chacra import models
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

models.init_model()


class SQLATask(celery.Task):
    """An abstract Celery Task that ensures that the connection the the
    database is closed on task completion"""
    abstract = True

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        models.remove()


@app.task(base=SQLATask)
def poll_repos():
    """
    Poll the repository objects that need to be updated and call the tasks
    that can create (or update) repositories with that information

    """
    logger.info('polling repos....')
    from chacra.models import Repo
    for r in Repo.query.all():
        if r.needs_update:
            logger.info("repo %s needs to be updated/created", r)
            # TODO: implement the actual call to RPM/DEB task here
    logger.info('completed repo polling')


app.conf.update(
    CELERYBEAT_SCHEDULE={
        'poll-repos': {
            'task': 'async.poll_repos',
            'schedule': timedelta(seconds=10),
        },
    },
)
