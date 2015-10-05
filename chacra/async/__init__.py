import pecan
from celery import Celery
import celery
from datetime import timedelta
from chacra import models
from chacra.util import repo_directory
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
    """An abstract Celery Task that ensures that the connection the the
    database is closed on task completion"""
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
        logger.info(r)
        logger.info(r.binaries)
        if r.needs_update:
            logger.info("repo %s needs to be updated/created", r)
            if r.binaries[0].name.endswith('rpm'):
                create_repo.delay([r.id])

    logger.info('completed repo polling')


@app.task(base=SQLATask)
def create_repo(repo_ids):
    """
    Go create or update repositories with specific IDs.
    """
    directories = ['SRPMS', 'noarch', 'x86_64']
    # get the root path for storing repos
    for _id in repo_ids:
        # TODO: Is it possible we can get an ID that doesn't exist anymore?
        repo = models.Repo.get(_id)
        logger.info("processing repository: %s", repo)
        project_name = repo.project.name

        # Determine paths for this repository
        root_path = os.path.join(pecan.conf.repos_root, project_name)
        relative_repo_path = '%s/%s/%s' % (repo.ref, repo.distro, repo.distro_version)
        abs_repo_path = os.path.join(root_path, relative_repo_path)
        repo_dirs = [os.path.join(abs_repo_path, d) for d in directories]

        # does this repo has a path? if so, it exists already, no need to
        # create structure
        if not repo.path or not os.path.exists(abs_repo_path):
            try:
                os.makedirs(abs_repo_path)
            except OSError as err:
                logger.warning('did not created dirs: %s', err)
                pass  # fixme! we should check if this exists
            for d in repo_dirs:
                if not os.path.exists(d):
                    os.makedirs(d)

        # now that structure is done, we need to symlink the RPMs that belong
        # to this repo so that we can create the metadata.
        for binary in repo.binaries:
            logger.warning(binary.__json__())
            source = binary.path
            destination_dir = os.path.join(abs_repo_path, repo_directory(binary.name))
            destination = os.path.join(destination_dir, binary.name)
            try:
                if not os.path.exists(destination):
                    os.symlink(source, destination)
            except OSError:
                logger.exception('could not symlink')

        for d in repo_dirs:
            subprocess.call(['createrepo', d])

        # Finally, set the repo path in the object and mark needs_update as False
        repo.path = abs_repo_path
        repo.needs_update = False
        models.commit()

app.conf.update(
    CELERYBEAT_SCHEDULE={
        'poll-repos': {
            'task': 'async.poll_repos',
            'schedule': timedelta(seconds=10),
        },
    },
)
