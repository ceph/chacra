import os
import subprocess

import pecan
import pytest
from celery.exceptions import Retry

from chacra import asynch, locks
from chacra.asynch import debian, rpm
from chacra.models import Binary, Project, Repo
from chacra.tests import conftest


lock_error = b"""The lock file '/opt/repos/ceph/db/lockfile' already exists. There might be another instance with the
same database dir running. To avoid locking overhead, only one process
can access the database at the same time. Do not delete the lock file unless
you are sure no other version is still running!
There have been errors!
"""

duplicate_error = b"""ERROR: '/opt/binaries/ceph-mgr_1.0_all.deb' cannot be included as 'pool/main/c/ceph/ceph-mgr_1.0_all.deb'.
Already existing files can only be included again, if they are the same, but:
md5 expected: 2e8b07e5f18da2ea10e07c490d628d14, got: 31f108a9a0ca65c657b21970d231790a
There have been errors!
"""

config_error = b"""No distribution definitions found in /opt/distributions/ceph/distributions!
There have been errors!
"""


class FakeReprepro(object):
    """
    Replaces ``subprocess.Popen``, failing for the binaries that have
    something to say in ``errors``. If that is a list, the items get consumed
    by each call until the list is empty, and then the command succeeds.
    """

    def __init__(self, errors=None):
        self.errors = errors or {}
        self.commands = []

    def __call__(self, command, **kw):
        self.commands.append(command)
        self.returncode = 0
        self.stderr = b''
        error = self.errors.get(os.path.basename(command[-1]))
        if isinstance(error, list):
            error = error.pop(0) if error else None
        if error:
            self.returncode = 255
            self.stderr = error
        return self

    def communicate(self):
        return b'', self.stderr


@pytest.fixture
def statuses(monkeypatch):
    """
    The statuses that got reported for repos
    """
    reported = []

    def post_status(status, repo_obj, _callback=None):
        reported.append(status)

    monkeypatch.setattr(asynch, 'post_status', post_status)
    return reported


@pytest.fixture
def no_sleep(monkeypatch):
    naps = []
    monkeypatch.setattr(debian.time, 'sleep', naps.append)
    return naps


class BuildTest(object):

    distro = 'ubuntu'
    distro_version = 'trusty'
    binaries = ['ceph_1.0_amd64.deb', 'ceph_1.0_arm64.deb', 'ceph-mgr_1.0_all.deb']

    @pytest.fixture(autouse=True)
    def setup_repo(self, session, tmpdir):
        pecan.conf.repos_root = str(tmpdir.mkdir('repos'))
        pecan.conf.distributions_root = str(tmpdir.mkdir('distributions'))
        pecan.conf.repo_build_retry_delay = 0
        project = Project('ceph')
        self.repo = Repo(project, 'firefly', self.distro, self.distro_version)
        for name in self.binaries:
            tmpdir.join(name).write('binary contents')
            Binary(
                name,
                project,
                repo=self.repo,
                ref='firefly',
                distro=self.distro,
                distro_version=self.distro_version,
                arch='x86_64',
                path=str(tmpdir.join(name)),
            )
        self.repo.needs_update = True
        self.repo.is_queued = True
        session.commit()
        self.session = session
        self.repo_path = os.path.join(
            pecan.conf.repos_root,
            'ceph/firefly/head/%s/%s/flavors/default' % (
                self.distro, self.distro_version)
        )
        yield
        # settings changed by the tests are "sticky"
        conftest.reload_config()

    def flags(self):
        self.session.Session.expire_all()
        repo = Repo.get(1)
        return dict(
            needs_update=repo.needs_update,
            is_queued=repo.is_queued,
            is_updating=repo.is_updating,
        )


class TestCreateDebRepo(BuildTest):

    @pytest.fixture(autouse=True)
    def reprepro(self, monkeypatch, no_sleep):
        self.reprepro = FakeReprepro()
        monkeypatch.setattr(subprocess, 'Popen', self.reprepro)

    def added(self):
        return sorted(os.path.basename(c[-1]) for c in self.reprepro.commands)

    def test_repo_is_ready(self, statuses):
        debian.create_deb_repo(1)
        assert self.added() == sorted(self.binaries)
        assert statuses == ['building', 'ready']
        assert self.flags() == dict(
            needs_update=False, is_queued=False, is_updating=False)
        assert Repo.get(1).path == self.repo_path
        assert locks.is_locked(1) is False

    def test_repo_is_already_being_built(self, statuses):
        lock = locks.RepoLock(1)
        assert lock.acquire() is True
        try:
            debian.create_deb_repo(1)
        finally:
            lock.release()
        assert self.reprepro.commands == []
        assert statuses == []
        assert self.flags()['needs_update'] is True
        assert self.flags()['is_queued'] is False

    def test_running_build_is_not_reset_by_a_second_task(self, statuses, monkeypatch):
        second_task = []
        reprepro = debian.reprepro

        def reprepro_with_second_task(command):
            # a second task shows up when the first one is adding binaries
            if not second_task:
                second_task.append(debian.create_deb_repo(1))
                assert self.flags() == dict(
                    needs_update=True, is_queued=False, is_updating=True)
            return reprepro(command)

        monkeypatch.setattr(debian, 'reprepro', reprepro_with_second_task)
        debian.create_deb_repo(1)
        # every binary was added once, by the first task
        assert self.added() == sorted(self.binaries)
        # the repo has to be built again, so it is not ready yet
        assert statuses == ['building']
        assert self.flags() == dict(
            needs_update=True, is_queued=False, is_updating=False)

    def test_reprepro_failure_is_not_ready(self, statuses):
        self.reprepro.errors = {'ceph_1.0_arm64.deb': config_error}
        with pytest.raises(Retry):
            debian.create_deb_repo(1)
        # the other binaries are still added
        assert self.added() == sorted(self.binaries)
        assert statuses == ['building']
        assert self.flags() == dict(
            needs_update=True, is_queued=True, is_updating=False)
        assert locks.is_locked(1) is False

    def test_reprepro_killed_is_not_ready(self, statuses):
        reprepro = self.reprepro

        def killed():
            reprepro.returncode = -9
            return b'', b''

        reprepro.communicate = killed
        with pytest.raises(Retry):
            debian.create_deb_repo(1)
        assert statuses == ['building']

    def test_reprepro_failure_gives_up(self, statuses):
        self.reprepro.errors = {'ceph_1.0_arm64.deb': config_error}
        debian.create_deb_repo.push_request(retries=3)
        try:
            debian.create_deb_repo(1)
        finally:
            debian.create_deb_repo.pop_request()
        assert statuses == ['building', 'failed']
        # looks like a build that was interrupted, won't be queued again
        assert self.flags() == dict(
            needs_update=True, is_queued=False, is_updating=True)
        assert locks.is_locked(1) is False

    def test_retries_are_configurable(self, statuses):
        pecan.conf.repo_build_retries = 0
        self.reprepro.errors = {'ceph_1.0_arm64.deb': config_error}
        debian.create_deb_repo(1)
        assert statuses == ['building', 'failed']

    def test_retry_is_ready(self, statuses):
        self.reprepro.errors = {'ceph_1.0_arm64.deb': [config_error]}
        with pytest.raises(Retry):
            debian.create_deb_repo(1)
        debian.create_deb_repo.push_request(retries=1)
        try:
            debian.create_deb_repo(1)
        finally:
            debian.create_deb_repo.pop_request()
        assert statuses == ['building', 'building', 'ready']
        assert self.flags() == dict(
            needs_update=False, is_queued=False, is_updating=False)

    def test_lock_contention_is_retried(self, statuses, no_sleep):
        self.reprepro.errors = {'ceph_1.0_arm64.deb': [lock_error, lock_error]}
        debian.create_deb_repo(1)
        assert self.added().count('ceph_1.0_arm64.deb') == 3
        assert no_sleep == [10, 10]
        assert statuses == ['building', 'ready']

    def test_lock_contention_that_does_not_go_away(self, statuses, no_sleep):
        pecan.conf.reprepro_lock_retries = 2
        pecan.conf.reprepro_lock_retry_delay = 1
        self.reprepro.errors = dict((name, lock_error) for name in self.binaries)
        with pytest.raises(Retry):
            debian.create_deb_repo(1)
        # does not go on with the rest of the binaries
        assert len(self.reprepro.commands) == 3
        assert no_sleep == [1, 1]
        assert statuses == ['building']
        assert self.flags()['needs_update'] is True

    def test_refused_binaries_are_ignored(self, statuses):
        self.reprepro.errors = {'ceph-mgr_1.0_all.deb': duplicate_error}
        debian.create_deb_repo(1)
        assert statuses == ['building', 'ready']

    def test_ignored_errors_are_configurable(self, statuses):
        pecan.conf.reprepro_ignored_errors = ['No distribution definitions']
        self.reprepro.errors = {'ceph_1.0_arm64.deb': config_error}
        debian.create_deb_repo(1)
        assert statuses == ['building', 'ready']

        self.reprepro.errors = {'ceph-mgr_1.0_all.deb': duplicate_error}
        with pytest.raises(Retry):
            debian.create_deb_repo(1)
        assert statuses == ['building', 'ready', 'building']

    def test_update_requested_while_building(self, statuses):
        def communicate():
            # what the update controller does
            self.session.Session.execute("UPDATE repos SET needs_update = true")
            self.session.commit()
            return b'', b''

        self.reprepro.communicate = communicate
        debian.create_deb_repo(1)
        assert statuses == ['building']
        assert self.flags() == dict(
            needs_update=True, is_queued=False, is_updating=False)

    def test_recreate_requested(self, statuses):
        os.makedirs(self.repo_path)
        leftover = os.path.join(self.repo_path, 'db')
        os.mkdir(leftover)
        locks.request_recreate(1)
        debian.create_deb_repo(1)
        assert os.path.exists(leftover) is False
        assert os.path.exists(self.repo_path) is True
        assert locks.recreate_requested(1) is False
        assert statuses == ['building', 'ready']

    def test_repo_does_not_exist(self, statuses):
        debian.create_deb_repo(2)
        assert statuses == []

    def test_disabled_repo(self, statuses):
        pecan.conf.repos = {'ceph': {'disabled': True}, '__force_dict__': True}
        debian.create_deb_repo(1)
        assert self.reprepro.commands == []
        assert statuses == ['building']
        assert self.flags() == dict(
            needs_update=False, is_queued=False, is_updating=False)
        assert locks.is_locked(1) is False


class TestCreateRpmRepo(BuildTest):

    distro = 'centos'
    distro_version = '9'
    binaries = ['ceph-1.0.x86_64.rpm', 'ceph-1.0.aarch64.rpm', 'ceph-1.0.src.rpm']

    @pytest.fixture(autouse=True)
    def createrepo(self, monkeypatch):
        self.commands = []
        self.returncode = 0

        def check_call(command):
            self.commands.append(command)
            if self.returncode:
                raise subprocess.CalledProcessError(self.returncode, command)

        monkeypatch.setattr(subprocess, 'check_call', check_call)

    def test_repo_is_ready(self, statuses):
        rpm.create_rpm_repo(1)
        assert len(self.commands) == 4
        assert os.path.islink(
            os.path.join(self.repo_path, 'aarch64/ceph-1.0.aarch64.rpm'))
        assert statuses == ['building', 'ready']
        assert self.flags() == dict(
            needs_update=False, is_queued=False, is_updating=False)
        assert locks.is_locked(1) is False

    def test_repo_is_already_being_built(self, statuses):
        lock = locks.RepoLock(1)
        assert lock.acquire() is True
        try:
            rpm.create_rpm_repo(1)
        finally:
            lock.release()
        assert self.commands == []
        assert os.path.exists(self.repo_path) is False
        assert statuses == []
        assert self.flags()['needs_update'] is True
        assert self.flags()['is_queued'] is False

    def test_createrepo_failure_is_not_ready(self, statuses):
        self.returncode = 1
        with pytest.raises(Retry):
            rpm.create_rpm_repo(1)
        assert statuses == ['building']
        assert self.flags() == dict(
            needs_update=True, is_queued=True, is_updating=False)
        assert locks.is_locked(1) is False

    def test_createrepo_failure_gives_up(self, statuses):
        self.returncode = 1
        rpm.create_rpm_repo.push_request(retries=3)
        try:
            rpm.create_rpm_repo(1)
        finally:
            rpm.create_rpm_repo.pop_request()
        assert statuses == ['building', 'failed']
        assert self.flags() == dict(
            needs_update=True, is_queued=False, is_updating=True)

    def test_update_requested_while_building(self, statuses, monkeypatch):
        def check_call(command):
            self.session.Session.execute("UPDATE repos SET needs_update = true")
            self.session.commit()

        monkeypatch.setattr(subprocess, 'check_call', check_call)
        rpm.create_rpm_repo(1)
        assert statuses == ['building']
        assert self.flags() == dict(
            needs_update=True, is_queued=False, is_updating=False)
