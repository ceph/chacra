import os
from chacra import locks


class TestRepoLock(object):

    def test_creates_the_directory(self, locks_root):
        assert os.path.exists(locks_root) is False
        lock = locks.RepoLock(1)
        assert lock.acquire() is True
        assert os.path.dirname(lock.path) == locks_root
        assert os.path.exists(lock.path) is True
        lock.release()

    def test_defaults_to_repos_root(self, tmpdir):
        from pecan import conf
        conf.locks_root = None
        conf.repos_root = str(tmpdir)
        assert locks.lock_path(1) == str(tmpdir.join('.locks', 'repo-1.lock'))

    def test_can_not_be_acquired_twice(self):
        first = locks.RepoLock(1)
        second = locks.RepoLock(1)
        assert first.acquire() is True
        assert second.acquire() is False
        first.release()

    def test_can_be_acquired_after_release(self):
        first = locks.RepoLock(1)
        second = locks.RepoLock(1)
        assert first.acquire() is True
        first.release()
        assert second.acquire() is True
        second.release()

    def test_release_is_safe_when_not_acquired(self):
        first = locks.RepoLock(1)
        second = locks.RepoLock(1)
        assert first.acquire() is True
        assert second.acquire() is False
        second.release()
        assert locks.is_locked(1) is True
        first.release()

    def test_repos_do_not_share_a_lock(self):
        first = locks.RepoLock(1)
        second = locks.RepoLock(2)
        assert first.acquire() is True
        assert second.acquire() is True
        first.release()
        second.release()

    def test_lock_file_that_got_removed(self):
        first = locks.RepoLock(1)
        assert first.acquire() is True
        locks.forget(1)
        second = locks.RepoLock(1)
        assert second.acquire() is True
        assert os.path.exists(second.path) is True
        first.release()
        second.release()


class TestIsLocked(object):

    def test_not_locked(self):
        assert locks.is_locked(1) is False

    def test_locked(self):
        lock = locks.RepoLock(1)
        lock.acquire()
        assert locks.is_locked(1) is True
        lock.release()
        assert locks.is_locked(1) is False

    def test_does_not_keep_the_lock(self):
        assert locks.is_locked(1) is False
        lock = locks.RepoLock(1)
        assert lock.acquire() is True
        lock.release()


class TestRecreate(object):

    def test_not_requested(self):
        assert locks.recreate_requested(1) is False

    def test_requested(self):
        locks.request_recreate(1)
        assert locks.recreate_requested(1) is True
        assert locks.recreate_requested(2) is False

    def test_cleared(self):
        locks.request_recreate(1)
        locks.clear_recreate(1)
        assert locks.recreate_requested(1) is False

    def test_clear_when_not_requested(self):
        locks.clear_recreate(1)
        assert locks.recreate_requested(1) is False


class TestForget(object):

    def test_removes_everything(self, locks_root):
        locks.RepoLock(1).acquire()
        locks.request_recreate(1)
        locks.forget(1)
        assert os.listdir(locks_root) == []

    def test_nothing_to_remove(self):
        locks.forget(1)
