import pecan
from celery import Celery
import celery
from datetime import timedelta
from chacra import models
from chacra import util
from chacra.metrics import Counter, Timer
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
    for r in models.Repo.query.filter_by(needs_update=True, is_queued=False).all():
        # this repo is being processed, do not pile up and try to get it
        # processed again until it is done doing work
        if r.is_updating:
            continue
        if r.needs_update:
            logger.info("repo %s needs to be updated/created", r)
            r.is_queued = True
            if r.type == 'rpm':
                create_rpm_repo.apply_async(
                    (r.id,),
                    countdown=pecan.conf.quiet_time,
                    queue='build_repos',
                    )
            elif r.type == 'deb':
                create_deb_repo.apply_async(
                    (r.id,),
                    countdown=pecan.conf.quiet_time,
                    queue='build_repos',
                    )
            else:
                _type = r.infer_type()
                if _type is None:
                    logger.warning('failed to infer repository type')
                    logger.warning('got a repository with an unknown type: %s', r)
                else:
                    logger.warning('inferred repo type as: %s', _type)
                    r.type = _type

            models.commit()

    logger.info('completed repo polling')


@app.task(base=SQLATask)
def create_deb_repo(repo_id):
    """
    Go create or update repositories with specific IDs.
    """
    # get the root path for storing repos
    # TODO: Is it possible we can get an ID that doesn't exist anymore?
    repo = models.Repo.get(repo_id)
    timer = Timer(__name__, suffix="create.deb.%s" % repo.metric_name)
    counter = Counter(__name__, suffix="create.deb.%s.binaries" % repo.metric_name)
    timer.start()
    logger.info("processing repository: %s", repo)
    if util.repository_is_disabled(repo.project.name):
        logger.info("will not process repository: %s", repo)
        repo.needs_update = False
        repo.is_queued = False
        models.commit()
        return

    # Determine paths for this repository
    paths = util.repo_paths(repo)

    # Before doing work that might take very long to complete, set the repo
    # path in the object, mark needs_update as False, and mark it as being
    # updated so we prevent piling up if other binaries are being posted
    repo.path = paths['absolute']
    repo.is_updating = True
    repo.is_queued = False
    repo.needs_update = False
    models.commit()

    # determine if other repositories might need to be queried to add extra
    # binaries (repos are tied to binaries which are all related with  refs,
    # archs, distros, and distro versions.
    conf_extra_repos = util.get_extra_repos(repo.project.name, repo.ref)
    combined_versions = util.get_combined_repos(repo.project.name)
    extra_binaries = []

    # See if there are any generic/universal binaries so that they can be
    # automatically added from the current project
    for binary in util.get_extra_binaries(
            repo.project.name,
            repo.distro,
            None,
            distro_versions=['generic', 'universal', 'any'],
            ref=repo.ref):
        extra_binaries.append(binary)

    for project_name, project_refs in conf_extra_repos.items():
        for ref in project_refs:
            logger.info('fetching binaries for project: %s, ref: %s', project_name, ref)
            found_binaries = util.get_extra_binaries(
                project_name,
                None,
                repo.distro_version,
                distro_versions=combined_versions,
                ref=ref if ref != 'all' else None
            )
            extra_binaries += found_binaries

            # See if there are any generic/universal binaries so that they can be
            # automatically added from projects coming from extra repos
            for binary in util.get_extra_binaries(
                    project_name,
                    repo.distro,
                    None,
                    distro_versions=['generic', 'universal', 'any'],
                    ref=ref if ref != 'all' else None):
                extra_binaries.append(binary)

    # check for the option to 'combine' repositories with different
    # debian/ubuntu versions
    for distro_version in combined_versions:
        logger.info(
            'fetching distro_version %s for project: %s',
            distro_version,
            repo.project.name
        )
        # When combining distro_versions we cannot filter by distribution as
        # well, otherwise it will be an impossible query. E.g. "get wheezy,
        # precise and trusty but only for the Ubuntu distro"
        extra_binaries += util.get_extra_binaries(
            repo.project.name,
            None,
            distro_version,
            ref=repo.ref
        )

    # try to create the absolute path to the repository if it doesn't exist
    util.makedirs(paths['absolute'])

    all_binaries = extra_binaries + [b for b in repo.binaries]
    timer.intermediate('collection')

    for binary in set(all_binaries):
        # XXX This is really not a good alternative but we are not going to be
        # using .changes for now although we can store it.
        if binary.extension == 'changes':
            continue
        try:
            commands = util.reprepro_commands(
                paths['absolute'],
                binary,
                distro_versions=combined_versions,
                fallback_version=repo.distro_version
            )
            counter += 1
        except KeyError:  # probably a tar.gz or similar file that should not be added directly
            continue
        for command in commands:
            logger.info('running command: %s', ' '.join(command))
            try:
                subprocess.check_call(command)
            except subprocess.CalledProcessError:
                logger.error('failed to add binary %s', binary.name)

    logger.info("finished processing repository: %s", repo)
    repo.is_updating = False
    models.commit()
    timer.stop()


@app.task(base=SQLATask)
def create_rpm_repo(repo_id):
    """
    Go create or update repositories with specific IDs.
    """
    directories = ['SRPMS', 'noarch', 'x86_64', 'aarch64']
    # get the root path for storing repos
    # TODO: Is it possible we can get an ID that doesn't exist anymore?
    repo = models.Repo.get(repo_id)
    timer = Timer(__name__, suffix="create.rpm.%s" % repo.metric_name)
    counter = Counter(__name__, suffix="create.rpm.%s.binaries" % repo.metric_name)
    timer.start()
    logger.info("processing repository: %s", repo)
    if util.repository_is_disabled(repo.project.name):
        logger.info("will not process repository: %s", repo)
        repo.needs_update = False
        repo.is_queued = False
        return

    # Determine paths for this repository
    paths = util.repo_paths(repo)
    repo_dirs = [os.path.join(paths['absolute'], d) for d in directories]

    # Before doing work that might take very long to complete, set the repo
    # path in the object and mark needs_update as False
    repo.path = paths['absolute']
    repo.is_updating = True
    repo.is_queued = False
    repo.needs_update = False
    models.commit()

    # this is safe to do, behind the scenes it is just trying to create them if
    # they don't exist and it will include the 'absolute' path
    for d in repo_dirs:
        util.makedirs(d)

    # now that structure is done, we need to symlink the RPMs that belong
    # to this repo so that we can create the metadata.
    conf_extra_repos = util.get_extra_repos(repo.project.name, repo.ref)
    extra_binaries = []
    for project_name, project_refs in conf_extra_repos.items():
        for ref in project_refs:
            extra_binaries += util.get_extra_binaries(
                project_name,
                repo.distro,
                repo.distro_version,
                ref=ref if ref != 'all' else None
            )

    all_binaries = extra_binaries + [b for b in repo.binaries]
    timer.intermediate('collection')
    for binary in all_binaries:
        source = binary.path
        arch_directory = util.infer_arch_directory(binary.name)
        destination_dir = os.path.join(paths['absolute'], arch_directory)
        destination = os.path.join(destination_dir, binary.name)
        counter += 1
        try:
            if not os.path.exists(destination):
                os.symlink(source, destination)
        except OSError:
            logger.exception('could not symlink')

    for d in repo_dirs:
        subprocess.check_call(['createrepo', d])

    logger.info("finished processing repository: %s", repo)
    repo.is_updating = False
    models.commit()
    timer.stop()


app.conf.update(
    CELERYBEAT_SCHEDULE={
        'poll-repos': {
            'task': 'async.poll_repos',
            'schedule': timedelta(
                seconds=pecan.conf.polling_cycle),
            'options': {'queue' : 'poll_repos'}
        },
    },
)
