from celery import shared_task
from pecan import conf
from chacra.asynch import base
from chacra import util
from chacra.metrics import Counter, Timer
import logging
import re
import subprocess
import time

logger = logging.getLogger(__name__)

# another reprepro process is using the database of the repository
lock_error = re.compile(r"lock file '.*' already exists")

# Errors that reprepro reports when it refuses a file because of what the file
# is, so trying again can't have a different result. These do not prevent
# a repository from being reported as ready. They are regular expressions that
# get matched against the error output, and can be overridden with the
# ``reprepro_ignored_errors`` configuration option.
ignored_errors = (
    # the pool has a file with the same name and different contents, like the
    # 'all' packages that get built (and uploaded) once per architecture
    r"Already existing files can only be included again",
    # a source package with a .dsc file that is not valid
    r"Missing '\w+' field in",
    # distro versions that are not in the distributions file
    r"Cannot find definition of distribution",
    # older reprepro versions can't handle ddeb files
    r"Unknown action 'includeddeb'",
)


@shared_task(base=base.SQLATask, bind=True)
def create_deb_repo(self, repo_id):
    """
    Go create or update repositories with specific IDs.
    """
    base.build_repo(self, repo_id, build)


def build(repo, paths):
    timer = Timer(__name__, suffix="create.deb.%s" % repo.metric_name)
    counter = Counter(__name__, suffix="create.deb.%s" % repo.metric_name)
    timer.start()

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
            ref=repo.ref,
            sha1=repo.sha1):
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

        if distro_version == repo.distro_version:
            logger.info('combine skipping same distro %s', distro_version)
            continue

        logger.info(
            'fetching distro_version %s for project: %s into repo %s',
            distro_version,
            repo.project.name,
            repo,
        )
        # When combining distro_versions we cannot filter by distribution as
        # well, otherwise it will be an impossible query. E.g. "get wheezy,
        # precise and trusty but only for the Ubuntu distro"
        extra_binaries += util.get_extra_binaries(
            repo.project.name,
            None,
            distro_version,
            ref=repo.ref,
            sha1=repo.sha1,
            flavor=repo.flavor,
        )

    # try to create the absolute path to the repository if it doesn't exist
    util.makedirs(paths['absolute'])

    all_binaries = extra_binaries + [b for b in repo.binaries]
    timer.intermediate('collection')
    logger.info('all_binaries: %s', [b.name for b in all_binaries])

    failed = []
    for binary in set(all_binaries):

        # sanity check
        for field in ['ref', 'sha1', 'distro', 'distro_version', 'flavor']:
            if getattr(binary, field, None) != getattr(repo, field, None):
                logger.warning('binary %s does not match repo %s', binary, repo)

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
            if not reprepro(command):
                logger.error('failed to add binary %s', binary.name)
                failed.append(binary.name)

    timer.stop()
    if failed:
        raise base.RepoBuildError(
            '%s binaries could not be added to %s: %s' % (
                len(failed), repo, ' '.join(sorted(set(failed))))
        )
    counter += 1


def reprepro(command):
    """
    Run a reprepro command, trying again when it fails because another
    reprepro process has the database of the repository locked. If it is
    still locked after all the retries there is no point in trying to add
    anything else, so that is an error.

    Returns ``False`` if the command failed, unless it is one of the errors
    that are configured to be ignored.
    """
    retries = getattr(conf, 'reprepro_lock_retries', 6)
    delay = getattr(conf, 'reprepro_lock_retry_delay', 10)
    attempt = 0
    while True:
        logger.info('running command: %s', ' '.join(command))
        result = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout, stderr = result.communicate()
        stdout = stdout.decode('utf-8', 'replace')
        stderr = stderr.decode('utf-8', 'replace')
        for line in stdout.split('\n'):
            logger.info(line)
        for line in stderr.split('\n'):
            logger.warning(line)
        if result.returncode == 0:
            return True
        if not lock_error.search(stderr):
            break
        if attempt >= retries:
            raise base.RepoBuildError(
                'reprepro database is still locked after %s retries' % retries
            )
        attempt += 1
        logger.warning(
            'reprepro database is locked, trying again in %s seconds (retry %s of %s)',
            delay, attempt, retries
        )
        time.sleep(delay)

    for error in getattr(conf, 'reprepro_ignored_errors', ignored_errors):
        if re.search(error, stderr):
            logger.warning('reprepro refused the file, ignoring: %s', command[-1])
            return True
    return False
