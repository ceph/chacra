from celery import shared_task
from chacra import models
from chacra.async import base, post_ready, post_building
from chacra import util
from chacra.metrics import Counter, Timer
import logging
import subprocess

logger = logging.getLogger(__name__)


@shared_task(base=base.SQLATask)
def create_deb_repo(repo_id):
    """
    Go create or update repositories with specific IDs.
    """
    # get the root path for storing repos
    # TODO: Is it possible we can get an ID that doesn't exist anymore?
    repo = models.Repo.get(repo_id)
    timer = Timer(__name__, suffix="create.deb.%s" % repo.metric_name)
    counter = Counter(__name__, suffix="create.deb.%s" % repo.metric_name)
    timer.start()
    post_building(repo)
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
    counter += 1
    post_ready(repo)
