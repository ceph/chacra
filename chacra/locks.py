"""
Per-repository locks, so that only one task at a time can work on the files
of a repository.

The ``is_updating`` and ``is_queued`` flags of a repository are just database
fields: anything can reset them, and they are left behind when a worker dies.
The lock is what tells if a build is really running. It is an ``flock`` on
a file, which the kernel releases when the process holding it goes away, so
it can't become stale.

Every process that builds repositories or serves the API needs to see the
same ``locks_root`` directory. It defaults to a ``.locks`` directory in
``repos_root``, which all of them have to share already.
"""
import errno
import fcntl
import logging
import os

from pecan import conf

from chacra import util

logger = logging.getLogger(__name__)


def locks_root():
    root = getattr(conf, 'locks_root', None)
    if root:
        return root
    return os.path.join(conf.repos_root, '.locks')


def lock_path(repo_id):
    return os.path.join(locks_root(), 'repo-%s.lock' % repo_id)


def recreate_path(repo_id):
    return os.path.join(locks_root(), 'repo-%s.recreate' % repo_id)


class RepoLock(object):
    """
    An exclusive, non-blocking lock for a repository::

        lock = RepoLock(repo.id)
        if lock.acquire():
            try:
                ...
            finally:
                lock.release()
    """

    def __init__(self, repo_id):
        self.repo_id = repo_id
        self.path = lock_path(repo_id)
        self.fd = None

    def acquire(self):
        """
        Returns ``True`` if the lock was acquired, ``False`` if something else
        is holding it.
        """
        util.makedirs(os.path.dirname(self.path))
        while True:
            fd = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o644)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except (IOError, OSError) as err:
                os.close(fd)
                if err.errno in (errno.EAGAIN, errno.EACCES):
                    return False
                raise
            # the file may have been removed (the repo got deleted) between
            # opening and locking it, that would be a lock on nothing
            try:
                if os.fstat(fd).st_ino == os.stat(self.path).st_ino:
                    self.fd = fd
                    return True
            except OSError as err:
                if err.errno != errno.ENOENT:
                    os.close(fd)
                    raise
            os.close(fd)

    def release(self):
        if self.fd is None:
            return
        try:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
        finally:
            os.close(self.fd)
            self.fd = None


def is_locked(repo_id):
    """
    Is there a build for this repository running right now?
    """
    lock = RepoLock(repo_id)
    if lock.acquire():
        lock.release()
        return False
    return True


def request_recreate(repo_id):
    """
    Leave a note for the next build of this repository, so that it removes
    the files of the repository before doing any work. Used when the
    repository can't be removed right away because it is being built.
    """
    util.makedirs(locks_root())
    with open(recreate_path(repo_id), 'w'):
        pass


def recreate_requested(repo_id):
    return os.path.exists(recreate_path(repo_id))


def _remove(path):
    try:
        os.remove(path)
    except OSError as err:
        if err.errno != errno.ENOENT:
            logger.exception('could not remove %s', path)


def clear_recreate(repo_id):
    _remove(recreate_path(repo_id))


def forget(repo_id):
    """
    Remove the files kept for a repository that is going away
    """
    _remove(recreate_path(repo_id))
    _remove(lock_path(repo_id))
