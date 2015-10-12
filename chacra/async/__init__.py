import pecan
from celery import Celery
import celery
from datetime import timedelta
from chacra import models
from chacra.util import infer_arch_directory, repo_paths, makedirs
import os
import logging
import subprocess
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
    """
    An abstract Celery Task that ensures that the connection the the
    database is closed on task completion

    .. note:: On logs, it may appear as there are errors in the transaction but
    this is not an error condition: SQLAlchemy rolls back the transaction if no
    change was done.
    """
    abstract = True

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        models.clear()


@app.task(base=SQLATask)
def poll_repos():
    """
    Poll the repository objects that need to be updated and call the tasks
    that can create (or update) repositories with that information

    """
    logger.info('polling repos....')
    for r in models.Repo.query.filter_by(needs_update=True).all():
        if r.needs_update:
            logger.info("repo %s needs to be updated/created", r)
            if r.type == 'rpm':
                create_rpm_repo.apply_async(
                    (r.id,),
                    countdown=pecan.conf.quiet_time)
            elif r.type == 'deb':
                create_deb_repo.apply_async(
                    (r.id,),
                    countdown=pecan.conf.quiet_time)

    logger.info('completed repo polling')


@app.task(base=SQLATask)
def create_deb_repo(repo_id):
    """
    Go create or update repositories with specific IDs.
    """
    # get the root path for storing repos
    # TODO: Is it possible we can get an ID that doesn't exist anymore?
    repo = models.Repo.get(repo_id)
    logger.info("processing repository: %s", repo)

    # Determine paths for this repository
    paths = repo_paths(repo)

    # try to create the absolute path to the repository if it doesn't exist
    makedirs(paths['absolute'])

    for binary in repo.binaries:
        logger.warning(binary.__json__())
        command = [
            'reprepro',
            '--confdir', '/etc',
            '-b', paths['absolute'],
            '-C', 'main',
            '--ignore=wrongdistribution',
            '--ignore=wrongversion',
            '--ignore=undefinedtarget',
            'includedeb', binary.distro_version,
            binary.path
        ]

        subprocess.check_call(command)

    # Finally, set the repo path in the object and mark needs_update as False
    repo.path = paths['absolute']
    repo.needs_update = False
    models.commit()


@app.task(base=SQLATask)
def create_rpm_repo(repo_id):
    """
    Go create or update repositories with specific IDs.
    """
    directories = ['SRPMS', 'noarch', 'x86_64']
    # get the root path for storing repos
    # TODO: Is it possible we can get an ID that doesn't exist anymore?
    repo = models.Repo.get(repo_id)
    logger.info("processing repository: %s", repo)

    # Determine paths for this repository
    paths = repo_paths(repo)
    repo_dirs = [os.path.join(paths['absolute'], d) for d in directories]

    # this is safe to do, behind the scenes it is just trying to create them if
    # they don't exist and it will include the 'absolute' path
    for d in repo_dirs:
        makedirs(d)

    # now that structure is done, we need to symlink the RPMs that belong
    # to this repo so that we can create the metadata.
    for binary in repo.binaries:
        logger.warning(binary.__json__())
        source = binary.path
        arch_directory = infer_arch_directory(binary.name)
        destination_dir = os.path.join(paths['absolute'], arch_directory)
        destination = os.path.join(destination_dir, binary.name)
        try:
            if not os.path.exists(destination):
                os.symlink(source, destination)
        except OSError:
            logger.exception('could not symlink')

    for d in repo_dirs:
        subprocess.check_call(['createrepo', d])

    # Finally, set the repo path in the object and mark needs_update as False
    repo.path = paths['absolute']
    repo.needs_update = False
    models.commit()


app.conf.update(
    CELERYBEAT_SCHEDULE={
        'poll-repos': {
            'task': 'async.poll_repos',
            'schedule': timedelta(
                seconds=pecan.conf.polling_cycle),
        },
    },
)
