import os
import pecan
import pytest
from chacra.models import Project, Repo, Binary
from chacra.compat import b_
from chacra import asynch, locks
from chacra.asynch import recurring
from chacra.tests import conftest


class TestRepoApiController(object):

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/']
    )
    def test_repo_archs(self, session, url):
        p = Project('foobar')
        Binary(
            'ceph-1.0.deb',
            p,
            distro='ubuntu',
            distro_version='trusty',
            arch='x86_64',
            sha1="head",
            ref="firefly",
        )
        session.commit()
        result = session.app.get(url)
        assert result.json['archs'] == ['x86_64']

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/repo/',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/repo/']
    )
    def test_repo_endpoint_deb(self, session, url):
        p = Project('foobar')
        Binary(
            'ceph-1.0.deb',
            p,
            distro='ubuntu',
            distro_version='trusty',
            arch='x86_64',
            sha1="head",
            ref="firefly",
        )
        session.commit()
        result = session.app.get(url)
        assert b_("deb") in result.body

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/centos/7/repo/',
             '/repos/foobar/firefly/head/centos/7/flavors/default/repo/']
    )
    def test_repo_endpoint_rpm(self, session, url):
        p = Project('foobar')
        Binary(
            'ceph-1.0.rpm',
            p,
            distro='centos',
            distro_version='7',
            arch='x86_64',
            sha1="head",
            ref="firefly",
        )
        session.commit()
        result = session.app.get(url)
        assert b_("[foobar]") in result.body
        assert b_("noarch") in result.body
        assert b_("SRPMS") in result.body

    @pytest.mark.parametrize(
        'url',
        ['/repos/foobar-opensuse/firefly/head/opensuse/15.1/repo/',
         '/repos/foobar-opensuse/firefly/head/opensuse/15.1/flavors/default/repo/']
    )
    def test_repo_endpoint_rpm_opensuse_sle(self, session, url):
        p = Project('foobar-opensuse')
        Binary(
            'ceph-1.0.rpm',
            p,
            distro='opensuse',
            distro_version='15.1',
            arch='x86_64',
            sha1="head",
            ref="firefly",
        )
        session.commit()
        result = session.app.get(url)
        assert b_('[foobar-opensuse]') in result.body
        assert b_("noarch") not in result.body
        assert b_("SRPMS") not in result.body

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/']
    )
    def test_repo_exists(self, session, url):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.get(url)
        assert result.status_int == 200
        assert result.json["distro_version"] == "trusty"
        assert result.json["distro"] == "ubuntu"
        assert result.json["ref"] == "firefly"
        assert result.json["sha1"] == "head"

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/']
    )
    def test_repo_exists_no_path(self, session, url):
        p = Project('foobar')
        Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        session.commit()
        result = session.app.get(url)
        assert result.status_int == 200
        assert result.json["distro_version"] == "trusty"
        assert result.json["distro"] == "ubuntu"
        assert result.json["ref"] == "firefly"
        assert result.json["sha1"] == "head"


    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/']
    )
    def test_repo_is_not_queued(self, session, url):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.get(url)
        assert result.status_int == 200
        assert result.json["is_queued"] is False

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/']
    )
    def test_repo_is_not_updating(self, session, url):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.get(url)
        assert result.status_int == 200
        assert result.json["is_updating"] is False

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/']
    )
    def test_repo_type(self, session, url):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.get(url)
        assert result.status_int == 200
        assert result.json["type"] is None

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/precise/',
             '/repos/foobar/firefly/head/ubuntu/precise/flavors/default/']
    )
    def test_distro_version_does_not_exist(self, session, url):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.get(url, expect_errors=True)
        assert result.status_int == 404

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/centos/trusty/',
             '/repos/foobar/firefly/head/centos/trusty/flavors/default/']
    )
    def test_distro_does_not_exist(self, session, url):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.get(url, expect_errors=True)
        assert result.status_int == 404

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/hammer/head/ubuntu/trusty/',
             '/repos/foobar/hammer/head/ubuntu/trusty/flavors/default/']
    )
    def test_ref_does_not_exist(self, session, url):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.get('/repos/foobar/hammer/head/ubuntu/trusty/', expect_errors=True)
        assert result.status_int == 404

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/sha1/ubuntu/trusty/',
             '/repos/foobar/firefly/sha1/ubuntu/trusty/flavors/default/']
    )
    def test_sha1_does_not_exist(self, session, url):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.get(url, expect_errors=True)
        assert result.status_int == 404

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/']
    )
    def test_extra_metadata_default(self, session, url):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.get(url)
        assert result.json['extra'] == {}

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/extra/',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/extra/']
    )
    def test_add_extra_metadata(self, session, url):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = "some_path"
        session.commit()
        repo_id = repo.id
        data = {'version': '0.94.8', 'distros': ['precise']}
        session.app.post_json(
            url,
            params=data,
        )
        updated_repo = Repo.get(repo_id)
        assert updated_repo.extra == {"version": "0.94.8", 'distros': ['precise']}

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/']
    )
    def test_update_single_field(self, session, url):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = "some_path"
        session.commit()
        repo_id = repo.id
        data = {"distro_version": "precise"}
        result = session.app.post_json(
            url,
            params=data,
        )
        assert result.status_int == 200
        updated_repo = Repo.get(repo_id)
        assert updated_repo.distro_version == "precise"
        assert result.json['distro_version'] == "precise"

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/']
    )
    def test_update_multiple_fields(self, session, url):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = "some_path"
        session.commit()
        repo_id = repo.id
        data = {"distro_version": "7", "distro": "centos"}
        result = session.app.post_json(
            url,
            params=data,
        )
        assert result.status_int == 200
        updated_repo = Repo.get(repo_id)
        assert updated_repo.distro_version == "7"
        assert updated_repo.distro == "centos"
        assert result.json['distro_version'] == "7"
        assert result.json['distro'] == "centos"

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/']
    )
    def test_update_invalid_fields(self, session, url):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = "some_path"
        session.commit()
        repo_id = repo.id
        data = {"bogus": "7", "distro": "centos"}
        result = session.app.post_json(
            url,
            params=data,
            expect_errors=True,
        )
        assert result.status_int == 400
        updated_repo = Repo.get(repo_id)
        assert updated_repo.distro == "ubuntu"

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/']
    )
    def test_update_empty_json(self, session, url):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.post_json(
            url,
            params=dict(),
            expect_errors=True,
        )
        assert result.status_int == 400

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/']
    )
    def test_update_invalid_field_value(self, session, url):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = "some_path"
        session.commit()
        data = {"distro": 123}
        result = session.app.post_json(
            url,
            params=data,
            expect_errors=True,
        )
        assert result.status_int == 400


class TestRepoCRUDOperations(object):

    def teardown_method(self):
        # settings changed by the tests are "sticky"
        conftest.reload_config()

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/update',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/update']
    )
    def test_update(self, session, tmpdir, url):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = "some_path"
        session.commit()
        repo.get(1)
        repo.needs_update = False
        session.commit()
        result = session.app.post_json(
            url,
            params={}
        )
        assert result.json['needs_update'] is True
        assert result.json['is_queued'] is False

    @pytest.mark.dmick
    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/'],
    )
    def test_create(self, session, url):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = "some_path"
        session.commit()
        repo.get(1)
        repo.needs_update = False
        session.commit()
        # create a raw type repo
        result = session.app.post_json(
            url,
            params={'type': 'raw'},
        )
        assert result.json['type'] == 'raw'

        # adding an rpm doesn't change the type
        Binary(
            'binary.rpm',
            p,
            repo,
            ref='firefly',
            sha1='head',
            flavor='default',
            distro='ubuntu',
            distro_version='trusty',
            arch='arm64',
        )
        session.commit()
        result = session.app.get(url)
        assert result.json['type'] == 'raw'

    @pytest.mark.dmick
    def test_raw_post_update(self, session, recorder, monkeypatch):
        pecan.conf.repos_root = '/tmp/root'
        url = '/repos/foobar/main/head/windows/999/'
        p = Project('foobar')
        repo = Repo(
            p,
            "main",
            "windows",
            "999",
            sha1="head",
        )
        session.commit()
        repo.get(1)
        # create a raw type repo
        result = session.app.post_json(
            url,
            params={
                'type': 'raw',
                'needs_update': False,
            },
        )
        assert result.json['type'] == 'raw'

        # check that update just marks it 'ready' immediately
        fake_post_status = recorder()
        monkeypatch.setattr(asynch, 'post_status', fake_post_status)
        result = session.app.post(url + 'update/')
        assert fake_post_status.recorder_calls[0]['args'][0] == 'ready'

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/update',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/update']
    )
    def test_update_head(self, session, tmpdir, url):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.head(url)
        assert result.status_int == 200

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/recreate',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/recreate']
    )
    def test_recreate(self, session, tmpdir, url):
        path = str(tmpdir)
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = path
        session.commit()
        result = session.app.post_json(url, params={})
        assert os.path.exists(path) is False
        assert result.json['needs_update'] is True
        assert result.json['is_queued'] is False

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/recreate',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/recreate']
    )
    def test_recreate_and_requeue(self, session, tmpdir, url):
        path = str(tmpdir)
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = path
        session.commit()
        repo = Repo.get(1)
        repo.is_queued = True
        session.commit()
        # the task has been queued for so long that it must be lost
        pecan.conf.queued_stale_after = -1
        result = session.app.post_json(url)
        assert os.path.exists(path) is False
        assert result.json['needs_update'] is True
        assert result.json['is_queued'] is False

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/recreate',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/recreate']
    )
    def test_recreate_invalid_path(self, session, tmpdir, url):
        path = str(tmpdir)
        invalid_path = os.path.join(path, 'invalid_path')
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = invalid_path
        session.commit()
        result = session.app.post_json(url)
        assert os.path.exists(path) is True
        assert result.json['needs_update'] is True

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/recreate',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/recreate']
    )
    def test_recreate_head(self, session, tmpdir, url):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.head(url)
        assert result.status_int == 200

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/recreate',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/recreate']
    )
    def test_recreate_head_not_found(self, session, tmpdir, url):
        # probably overkill
        result = session.app.head(
            url,
            expect_errors=True,
        )
        assert result.status_int == 404

    @pytest.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/recreate',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/recreate']
    )
    def test_create_head_not_found(self, session, tmpdir, url):
        # probably overkill
        result = session.app.head(
            url,
            expect_errors=True,
        )
        assert result.status_int == 404


update_urls = [
    '/repos/foobar/firefly/head/ubuntu/trusty/update',
    '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/update',
]

recreate_urls = [
    '/repos/foobar/firefly/head/ubuntu/trusty/recreate',
    '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/recreate',
]


class TestUpdateWhileBuilding(object):

    def setup_method(self):
        self.repo = Repo(
            Project('foobar'),
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        self.repo.type = 'deb'

    def teardown_method(self):
        # settings changed by the tests are "sticky"
        conftest.reload_config()

    def building(self, session, tmpdir):
        """
        Leave the repo in the same state as when a task is building it
        """
        self.repo.path = str(tmpdir.mkdir('repo'))
        self.repo.needs_update = False
        self.repo.is_updating = True
        session.commit()
        lock = locks.RepoLock(1)
        assert lock.acquire() is True
        return lock

    def queued_tasks(self, monkeypatch, recorder):
        pecan.conf.quiet_time = 1
        queued = recorder()
        monkeypatch.setattr(recurring.debian.create_deb_repo, 'apply_async', queued)
        monkeypatch.setattr(recurring.rpm.create_rpm_repo, 'apply_async', queued)
        return queued.recorder_calls

    @pytest.mark.parametrize('url', update_urls)
    def test_update_does_not_reset_a_running_build(self, session, tmpdir, url):
        lock = self.building(session, tmpdir)
        try:
            result = session.app.post_json(url, params={})
        finally:
            lock.release()
        assert result.json['needs_update'] is True
        assert result.json['is_updating'] is True

    @pytest.mark.parametrize('url', update_urls)
    def test_update_does_not_queue_a_concurrent_build(
            self, session, tmpdir, monkeypatch, recorder, url):
        queued = self.queued_tasks(monkeypatch, recorder)
        lock = self.building(session, tmpdir)
        try:
            session.app.post_json(url, params={})
            recurring.poll_repos()
            assert queued == []
            assert Repo.get(1).is_queued is False
        finally:
            lock.release()

        # the build completes, now it can get queued
        repo = Repo.get(1)
        repo.is_updating = False
        session.commit()
        recurring.poll_repos()
        assert len(queued) == 1
        assert queued[0]['args'][0] == (1,)
        assert Repo.get(1).is_queued is True

    @pytest.mark.parametrize('url', update_urls)
    def test_update_resets_stale_is_updating(self, session, tmpdir, url):
        # a worker that died while building the repo
        self.building(session, tmpdir).release()
        result = session.app.post_json(url, params={})
        assert result.json['needs_update'] is True
        assert result.json['is_updating'] is False

    @pytest.mark.parametrize('url', update_urls)
    def test_update_does_not_reset_a_queued_build(
            self, session, monkeypatch, recorder, url):
        queued = self.queued_tasks(monkeypatch, recorder)
        self.repo.is_queued = True
        session.commit()
        result = session.app.post_json(url, params={})
        assert result.json['needs_update'] is True
        assert result.json['is_queued'] is True
        recurring.poll_repos()
        assert queued == []

    @pytest.mark.parametrize('url', update_urls)
    def test_update_resets_stale_is_queued(self, session, url):
        self.repo.is_queued = True
        session.commit()
        session.Session.execute(
            "UPDATE repos SET modified = LOCALTIMESTAMP - interval '2 hours'"
        )
        session.commit()
        result = session.app.post_json(url, params={})
        assert result.json['needs_update'] is True
        assert result.json['is_queued'] is False

    @pytest.mark.parametrize('url', update_urls)
    def test_stale_is_queued_is_configurable(self, session, url):
        pecan.conf.queued_stale_after = 3 * 60 * 60
        self.repo.is_queued = True
        session.commit()
        session.Session.execute(
            "UPDATE repos SET modified = LOCALTIMESTAMP - interval '2 hours'"
        )
        session.commit()
        result = session.app.post_json(url, params={})
        assert result.json['is_queued'] is True

    @pytest.mark.parametrize('url', recreate_urls)
    def test_recreate_does_not_remove_a_running_build(self, session, tmpdir, url):
        lock = self.building(session, tmpdir)
        path = self.repo.path
        try:
            result = session.app.post_json(url, params={})
            assert os.path.exists(path) is True
            assert locks.recreate_requested(1) is True
        finally:
            lock.release()
        assert result.json['needs_update'] is True
        assert result.json['is_updating'] is True

    @pytest.mark.parametrize('url', recreate_urls)
    def test_recreate_resets_stale_is_updating(self, session, tmpdir, url):
        self.building(session, tmpdir).release()
        path = self.repo.path
        result = session.app.post_json(url, params={})
        assert os.path.exists(path) is False
        assert locks.recreate_requested(1) is False
        assert locks.is_locked(1) is False
        assert result.json['needs_update'] is True
        assert result.json['is_updating'] is False

    @pytest.mark.parametrize('url', recreate_urls)
    def test_recreate_does_not_reset_a_queued_build(self, session, tmpdir, url):
        path = str(tmpdir.mkdir('repo'))
        self.repo.path = path
        self.repo.is_queued = True
        session.commit()
        result = session.app.post_json(url, params={})
        assert os.path.exists(path) is False
        assert result.json['needs_update'] is True
        assert result.json['is_queued'] is True
