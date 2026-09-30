import logging
import shutil

import celery
import pecan

from chacra import asynch, locks, models, util

logger = logging.getLogger(__name__)


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


class RepoBuildError(Exception):
    """
    The repository could not be built completely, it must not be advertised as
    ready.
    """


def build_repo(task, repo_id, build):
    """
    Common steps for the tasks that create (or update) a repository, calling
    ``build(repo, paths)`` to do the actual work for the type of repository.

    Only one task at a time is allowed to work on a repository. Tools like
    reprepro and createrepo_c produce incomplete repositories when they run
    concurrently on the same directory. If the repository is already being
    built it gets marked again as needing an update, so that it is picked up
    when the running build is done.

    A repository is reported as ready only when ``build`` didn't fail.
    Otherwise the task is retried a few times and, if it keeps failing, the
    repository is left marked as ``needs_update`` and ``is_updating``, just
    like a build that got interrupted, until a new update is requested for it.
    """
    repo = models.Repo.get(repo_id)
    if repo is None:
        logger.warning('repository with id %s does not exist anymore', repo_id)
        return

    lock = locks.RepoLock(repo_id)
    if not lock.acquire():
        logger.info('%s is being built by another task, will not process it', repo)
        repo.needs_update = True
        repo.is_queued = False
        models.commit()
        return

    try:
        _build_repo(task, repo, build)
    finally:
        lock.release()


def _build_repo(task, repo, build):
    repo_id = repo.id
    asynch.post_building(repo)
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

    try:
        if locks.recreate_requested(repo_id):
            logger.info('removing repository path: %s', paths['absolute'])
            shutil.rmtree(paths['absolute'], ignore_errors=True)
            locks.clear_recreate(repo_id)
        build(repo, paths)
        failed = False
    except Exception:
        logger.exception('failed to build repository: %s', repo)
        # the session may be unusable if the database caused the failure
        models.rollback()
        failed = True

    if failed:
        return build_failed(task, models.Repo.get(repo_id))

    logger.info("finished processing repository: %s", repo)
    repo.is_updating = False
    models.commit()
    if repo.needs_update:
        # an update was requested while this was building. The repo might be
        # missing binaries that got added after the build started
        logger.info('%s needs to be updated again, will not report it as ready', repo)
        return
    asynch.post_ready(repo)


def build_failed(task, repo):
    retries = getattr(pecan.conf, 'repo_build_retries', 3)
    delay = getattr(pecan.conf, 'repo_build_retry_delay', 120)
    repo.needs_update = True

    if task.request.retries < retries:
        logger.warning(
            '%s will be built again in %s seconds (retry %s of %s)',
            repo, delay, task.request.retries + 1, retries
        )
        repo.is_updating = False
        repo.is_queued = True
        models.commit()
        raise task.retry(countdown=delay, max_retries=retries)

    # Do not clear is_updating. There is nothing else to try, and leaving the
    # repo as-is will prevent it from getting queued over and over, and from
    # being consumed as if it was complete.
    logger.error(
        '%s could not be built after %s retries, giving up until a new update is requested',
        repo, retries
    )
    repo.is_updating = True
    repo.is_queued = False
    models.commit()
    asynch.post_failed(repo)
