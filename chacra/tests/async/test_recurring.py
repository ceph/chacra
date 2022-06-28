import datetime
import os
import pytest
from pecan import conf
from chacra.tests import conftest
from chacra.asynch import recurring
from chacra.models import Repo, Project, Binary
from chacra.models.repos import (
    add_timestamp_listeners as add_repo_listeners,
    remove_timestamp_listeners as remove_repo_listeners
)
from chacra.models.binaries import (
    add_timestamp_listeners as add_binary_listeners,
    remove_timestamp_listeners as remove_binary_listeners
)

@pytest.fixture
def no_update_timestamp():
    remove_repo_listeners()
    remove_binary_listeners()
    yield
    add_repo_listeners()
    add_binary_listeners()


class TestPurgeRepos(object):

    def setup(self):
        self.p = Project('ceph')
        self.repo = Repo(
            self.p,
            ref='firefly',
            distro='centos',
            distro_version='7',
            )

        self.now = datetime.datetime.utcnow()
        # slightly old
        self.one_minute = self.now - datetime.timedelta(minutes=1)
        # really old
        self.three_weeks_ago = self.now - datetime.timedelta(weeks=3)

        self.repo.modified = self.three_weeks_ago
        conf.purge_repos = True

    def teardown(self):
        # callback settings added in test_post_request are "sticky", this
        # ensures they are reset for other tests that rely on pristine conf
        # settings
        conftest.reload_config()

    def test_gets_rid_of_old_repos(self, session, no_update_timestamp):
        session.commit()
        recurring.purge_repos()
        assert Repo.query.all() == []

    def test_does_not_get_rid_of_old_repos_by_ref_configured_in_days(self, session, no_update_timestamp):
        conf.purge_rotation = {'ceph': {'ref': {'firefly': {'days': 70}}}, '__force_dict__': True}
        session.commit()
        recurring.purge_repos()
        assert len(Repo.query.all()) == 1

    def test_does_not_get_rid_of_old_repos_by_ref_configured_with_offset(self, session, no_update_timestamp):
        conf.purge_rotation = {'ceph': {'ref': {'firefly': {'keep_minimum': 1}}}, '__force_dict__': True}
        session.commit()
        recurring.purge_repos()
        assert len(Repo.query.all()) == 1

    def test_does_not_get_rid_of_old_repos_by_flavor_configured_in_days(self, session, no_update_timestamp):
        conf.purge_rotation = {'ceph': {'flavor': {'default': {'days': 70}}}, '__force_dict__': True}
        session.commit()
        recurring.purge_repos()
        assert len(Repo.query.all()) == 1

    def test_does_not_get_rid_of_old_repos_by_flavor_configured_with_offset(self, session, no_update_timestamp):
        conf.purge_rotation = {'ceph': {'flavor': {'default': {'keep_minimum': 1}}}, '__force_dict__': True}
        session.commit()
        recurring.purge_repos()
        assert len(Repo.query.all()) == 1


    def test_get_rid_of_new_and_old_repos_by_ref_configured_in_days(self, session, no_update_timestamp):
        Repo(
            project=Project('nfs-ganesha'),
            ref='next',
            distro='centos',
            distro_version='7',
            flavor='ceph_main',
        )
        # cause lifespan for this repo to be 0 days, thus remove it
        conf.purge_rotation = {'nfs-ganesha': {'ref': {'next': {'days': 0}}}, '__force_dict__': True}
        session.commit()
        recurring.purge_repos()
        assert len(Repo.query.all()) == 0

    def test_get_rid_of_old_but_keep_new_by_ref_configured_with_offset(self, session, no_update_timestamp):
        repo = Repo(
            project=Project('nfs-ganesha'),
            ref='next',
            distro='centos',
            distro_version='7',
            flavor='ceph_main',
        )
        repo.modified = self.one_minute

        conf.purge_rotation = {'nfs-ganesha': {'ref': {'next': {'keep_minimum': 0}}}, '__force_dict__': True}
        session.commit()
        recurring.purge_repos()
        assert len(Repo.query.all()) == 1

    def test_get_rid_of_new_and_old_repos_by_flavor_configured_in_days(self, session, no_update_timestamp):
        repo = Repo(
            project=Project('nfs-ganesha'),
            ref='next',
            distro='centos',
            distro_version='7',
            flavor='ceph_main',
        )
        repo.modified = self.one_minute

        # cause lifespan for this repo to be 0 days, thus remove it
        conf.purge_rotation = {'nfs-ganesha': {'flavor': {'ceph_main': {'days': 0}}}, '__force_dict__': True}
        session.commit()
        recurring.purge_repos()
        assert len(Repo.query.all()) == 0

    def test_get_rid_of_old_but_keep_new_repo_by_flavor_configured_with_offset(self, session, no_update_timestamp):
        repo = Repo(
            project=Project('nfs-ganesha'),
            ref='next',
            distro='centos',
            distro_version='7',
            flavor='ceph_main',
        )
        repo.modified = self.one_minute

        conf.purge_rotation = {'nfs-ganesha': {'flavor': {'ceph_main': {'keep_minimum': 0}}}, '__force_dict__': True}
        session.commit()
        recurring.purge_repos()
        assert len(Repo.query.all()) == 1

    def test_does_not_get_rid_of_old_repos_by_flavor_and_ref(self, session, no_update_timestamp):
        conf.purge_rotation = {'ceph': {'flavor': {'default': {'keep_minimum': 1}}, 'ref': {'firefly': {'days': 70}}}, '__force_dict__': True}
        session.commit()
        recurring.purge_repos()
        assert len(Repo.query.all()) == 1

    def test_keeps_new_repo_by_flavor_with_days(self, session, no_update_timestamp):
        Repo(
            project=Project('nfs-ganesha'),
            ref='next',
            distro='centos',
            distro_version='7',
            flavor='ceph_main',
        )

        conf.purge_rotation = {'nfs-ganesha': {'flavor': {'ceph_main': {'keep_minimum': 0, 'days': 70}}}, '__force_dict__': True}
        session.commit()
        recurring.purge_repos()
        assert len(Repo.query.all()) == 1

    def test_keeps_new_repo_by_flavor_with_offset(self, session, no_update_timestamp):
        Repo(
            project=Project('nfs-ganesha'),
            ref='next',
            distro='centos',
            distro_version='7',
            flavor='ceph_main',
        )

        conf.purge_rotation = {'nfs-ganesha': {'flavor': {'ceph_main': {'keep_minimum': 1, 'days': 0}}}, '__force_dict__': True}
        session.commit()
        recurring.purge_repos()
        assert len(Repo.query.all()) == 1


    def test_keeps_new_repo_by_flavor_with_offset_bad_ref_days(self, session, no_update_timestamp):
        Repo(
            project=Project('nfs-ganesha'),
            ref='next',
            distro='centos',
            distro_version='7',
            flavor='ceph_main',
        )

        conf.purge_rotation = {'nfs-ganesha': {'flavor': {'ceph_main': {'keep_minimum': 1}}, 'ref': {'next': {'days': 0}}}, '__force_dict__': True}
        session.commit()
        recurring.purge_repos()
        assert len(Repo.query.all()) == 1

    def test_keeps_new_repo_by_ref_with_days_bad_flavor_offset(self, session, no_update_timestamp):
        Repo(
            project=Project('nfs-ganesha'),
            ref='next',
            distro='centos',
            distro_version='7',
            flavor='ceph_main',
        )

        conf.purge_rotation = {'nfs-ganesha': {'flavor': {'ceph_main': {'keep_minimum': 0}}, 'ref': {'next': {'days': 70}}}, '__force_dict__': True}
        session.commit()
        recurring.purge_repos()
        assert len(Repo.query.all()) == 1


    def test_get_rid_of_new_repo_with_ref_and_flavor(self, session, no_update_timestamp):
        Repo(
            project=Project('nfs-ganesha'),
            ref='next',
            distro='centos',
            distro_version='7',
            flavor='ceph_main',
        )

        conf.purge_rotation = {'nfs-ganesha': {'flavor': {'ceph_main': {'keep_minimum': 0}}, 'ref': {'next': {'days': 0}}}, '__force_dict__': True}
        session.commit()
        recurring.purge_repos()
        assert len(Repo.query.all()) == 0

    def test_get_rid_of_new_repos_without_offset(self, session, no_update_timestamp):
        Repo(
            project=Project('nfs-ganesha'),
            ref='next',
            distro='centos',
            distro_version='7',
            flavor='ceph_main',
        )

        conf.purge_rotation = {'nfs-ganesha': {'flavor': {'ceph_main': {'days': 0}}, 'ref': {'next': {'days': 0}}}, '__force_dict__': True}
        session.commit()
        recurring.purge_repos()
        assert len(Repo.query.all()) == 0


    def test_get_rid_of_new_and_old_repos_without_days(self, session, no_update_timestamp):
        repo = Repo(
            project=Project('nfs-ganesha'),
            ref='next',
            distro='centos',
            distro_version='7',
            flavor='ceph_main',
        )
        repo.modified = self.three_weeks_ago

        conf.purge_rotation = {'nfs-ganesha': {'flavor': {'ceph_main': {'keep_minimum': 0}}, 'ref': {'next': {'keep_minimum': 0}}}, '__force_dict__': True}
        session.commit()
        recurring.purge_repos()
        assert len(Repo.query.all()) == 0

    def test_gets_rid_of_other_repos(self, session, no_update_timestamp):
        Repo(
            self.p,
            ref='hammer',
            distro='centos',
            distro_version='7',
        )

        conf.purge_rotation = {'ceph': {'ref': {'firefly': {'keep_minimum': 1}}}, '__force_dict__': True}
        session.commit()
        recurring.purge_repos()
        assert Repo.query.first().ref == 'firefly'

    def test_gets_rid_of_old_repos_paths(self, session, no_update_timestamp, tmpdir):
        repo_path = str(tmpdir)
        package = tmpdir.join('ceph-1.0.rpm')
        package.write("101010101010")
        self.repo.path = str(repo_path)
        session.commit()
        recurring.purge_repos()
        assert os.path.exists(repo_path) is False

    def test_leaves_newer_repos_behind(self, session, no_update_timestamp):
        self.repo.modified = self.now
        session.commit()
        recurring.purge_repos()
        assert len(Repo.query.all()) == 1

    def test_deletes_related_binaries_as_well(self, session, no_update_timestamp, tmpdir):
        p = tmpdir.join('binary')
        p.write('contents')
        Binary(
            'ceph-10.0.0.rpm', self.p, distro='centos',
            distro_version='6',
            arch='i386',
            path=str(p),
            repo=self.repo
        )
        session.commit()
        assert len(Binary.query.all()) == 1
        recurring.purge_repos()
        assert len(Binary.query.all()) == 0

    def test_ignores_binaries_that_do_not_exist(self, session, no_update_timestamp, tmpdir):
        p = tmpdir.join('binary')
        p.write_text(u'contents', encoding='utf-8')
        Binary(
            'ceph-10.0.0.rpm', self.p, distro='centos',
            distro_version='6',
            arch='i386',
            path=p.strpath,
            repo=self.repo
        )
        session.commit()
        # remove the binary, to ensure that the purge can continue
        os.remove(str(p))
        assert len(Binary.query.all()) == 1
        recurring.purge_repos()
        assert len(Binary.query.all()) == 0

    def test_if_disabled_it_does_not_purge_binaries(self, session, no_update_timestamp, tmpdir):
        conf.purge_repos = False
        p = tmpdir.join('binary')
        p.write('contents')
        Binary(
            'ceph-10.0.0.rpm', self.p, distro='centos',
            distro_version='6',
            arch='i386',
            path=str(p),
            repo=self.repo
        )
        session.commit()
        recurring.purge_repos()
        assert len(Binary.query.all()) == 1

    def test_does_not_get_rid_of_old_repos(self, session, no_update_timestamp):
        conf.purge_repos = False
        session.commit()
        recurring.purge_repos()
        assert len(Repo.query.all()) == 1


