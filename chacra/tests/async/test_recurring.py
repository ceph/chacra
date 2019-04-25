import datetime
import os
from pecan import conf
from chacra.tests import conftest
from chacra.async import recurring
from chacra.models import Repo, Project, Binary


class TestPurgeRepos(object):

    def setup(self):
        self.p = Project('ceph')
        self.repo = Repo(
            self.p,
            ref='firefly',
            distro='centos',
            distro_version='7',
            )
        # this is so very very painful to setup because it is just impossible
        # to patch sqlalchemy event listeners which set the modified attribute
        # on these objects. Instead we are able to patch datetime, so we mangle
        # it to assert that purging will work
        self.now = datetime.datetime.utcnow()
        self.old = self.now - datetime.timedelta(weeks=3)
        conf.purge_repos = True

    def teardown(self):
        # callback settings added in test_post_request are "sticky", this
        # ensures they are reset for other tests that rely on pristine conf
        # settings
        conftest.reload_config()

    def test_gets_rid_of_old_repos(self, session, fake, monkeypatch):
        fake_datetime = fake(utcnow=lambda: self.old, now=self.now)
        monkeypatch.setattr(datetime, 'datetime', fake_datetime)
        session.commit()
        recurring.purge_repos(_now=self.now)
        assert Repo.query.all() == []

    def test_does_not_get_rid_of_old_repos_by_ref_configured_in_days(self, session, fake, monkeypatch):
        conf.purge_rotation = {'ceph': {'ref': {'firefly': {'days': 70}}}, '__force_dict__': True}
        fake_datetime = fake(utcnow=lambda: self.old, now=self.now)
        monkeypatch.setattr(datetime, 'datetime', fake_datetime)
        session.commit()
        recurring.purge_repos(_now=self.now)
        assert len(Repo.query.all()) == 1

    def test_does_not_get_rid_of_old_repos_by_ref_configured_with_offset(self, session, fake, monkeypatch):
        conf.purge_rotation = {'ceph': {'ref': {'firefly': {'keep_minimum': 1}}}, '__force_dict__': True}
        fake_datetime = fake(utcnow=lambda: self.old, now=self.now)
        monkeypatch.setattr(datetime, 'datetime', fake_datetime)
        session.commit()
        recurring.purge_repos(_now=self.now)
        assert len(Repo.query.all()) == 1

    def test_does_not_get_rid_of_old_repos_by_flavor_configured_in_days(self, session, fake, monkeypatch):
        conf.purge_rotation = {'ceph': {'flavor': {'default': {'days': 70}}}, '__force_dict__': True}
        fake_datetime = fake(utcnow=lambda: self.old, now=self.now)
        monkeypatch.setattr(datetime, 'datetime', fake_datetime)
        session.commit()
        recurring.purge_repos(_now=self.now)
        assert len(Repo.query.all()) == 1

    def test_does_not_get_rid_of_old_repos_by_flavor_configured_with_offset(self, session, fake, monkeypatch):
        conf.purge_rotation = {'ceph': {'flavor': {'default': {'keep_minimum': 1}}}, '__force_dict__': True}
        fake_datetime = fake(utcnow=lambda: self.old, now=self.now)
        monkeypatch.setattr(datetime, 'datetime', fake_datetime)
        session.commit()
        recurring.purge_repos(_now=self.now)
        assert len(Repo.query.all()) == 1

    def test_get_rid_of_new_and_old_repos_by_ref_configured_in_days(self, session, fake, monkeypatch):
        Repo(
            project=Project('nfs-ganesha'),
            ref='next',
            distro='centos',
            distro_version='7',
            flavor='ceph_master',
        )

        conf.purge_rotation = {'nfs-ganesha': {'ref': {'next': {'days': 0}}}, '__force_dict__': True}
        fake_datetime = fake(utcnow=lambda: self.old, now=self.now)
        monkeypatch.setattr(datetime, 'datetime', fake_datetime)
        session.commit()
        recurring.purge_repos(_now=self.now)
        assert len(Repo.query.all()) == 0

    def test_get_rid_of_new_and_old_repos_by_ref_configured_with_offset(self, session, fake, monkeypatch):
        Repo(
            project=Project('nfs-ganesha'),
            ref='next',
            distro='centos',
            distro_version='7',
            flavor='ceph_master',
        )

        conf.purge_rotation = {'nfs-ganesha': {'ref': {'next': {'keep_minimum': 0}}}, '__force_dict__': True}
        fake_datetime = fake(utcnow=lambda: self.old, now=self.now)
        monkeypatch.setattr(datetime, 'datetime', fake_datetime)
        session.commit()
        recurring.purge_repos(_now=self.now)
        assert len(Repo.query.all()) == 0

    def test_get_rid_of_new_and_old_repos_by_flavor_configured_in_days(self, session, fake, monkeypatch):
        Repo(
            project=Project('nfs-ganesha'),
            ref='next',
            distro='centos',
            distro_version='7',
            flavor='ceph_master',
        )

        conf.purge_rotation = {'nfs-ganesha': {'flavor': {'ceph_master': {'days': 0}}}, '__force_dict__': True}
        fake_datetime = fake(utcnow=lambda: self.old, now=self.now)
        monkeypatch.setattr(datetime, 'datetime', fake_datetime)
        session.commit()
        recurring.purge_repos(_now=self.now)
        assert len(Repo.query.all()) == 0

    def test_get_rid_of_new_and_old_repos_by_flavor_configured_with_offset(self, session, fake, monkeypatch):
        Repo(
            project=Project('nfs-ganesha'),
            ref='next',
            distro='centos',
            distro_version='7',
            flavor='ceph_master',
        )

        conf.purge_rotation = {'nfs-ganesha': {'flavor': {'ceph_master': {'keep_minimum': 0}}}, '__force_dict__': True}
        fake_datetime = fake(utcnow=lambda: self.old, now=self.now)
        monkeypatch.setattr(datetime, 'datetime', fake_datetime)
        session.commit()
        recurring.purge_repos(_now=self.now)
        assert len(Repo.query.all()) == 0

    def test_does_not_get_rid_of_old_repos_by_flavor_and_ref(self, session, fake, monkeypatch):
        conf.purge_rotation = {'ceph': {'flavor': {'default': {'keep_minimum': 1}}, 'ref': {'firefly': {'days': 70}}}, '__force_dict__': True}
        fake_datetime = fake(utcnow=lambda: self.old, now=self.now)
        monkeypatch.setattr(datetime, 'datetime', fake_datetime)
        session.commit()
        recurring.purge_repos(_now=self.now)
        assert len(Repo.query.all()) == 1

    def test_keeps_new_repo_by_flavor_with_days(self, session, fake, monkeypatch):
        Repo(
            project=Project('nfs-ganesha'),
            ref='next',
            distro='centos',
            distro_version='7',
            flavor='ceph_master',
        )

        conf.purge_rotation = {'nfs-ganesha': {'flavor': {'ceph_master': {'keep_minimum': 0, 'days': 70}}}, '__force_dict__': True}
        fake_datetime = fake(utcnow=lambda: self.old, now=self.now)
        monkeypatch.setattr(datetime, 'datetime', fake_datetime)
        session.commit()
        recurring.purge_repos(_now=self.now)
        assert len(Repo.query.all()) == 1

    def test_keeps_new_repo_by_flavor_with_offset(self, session, fake, monkeypatch):
        Repo(
            project=Project('nfs-ganesha'),
            ref='next',
            distro='centos',
            distro_version='7',
            flavor='ceph_master',
        )

        conf.purge_rotation = {'nfs-ganesha': {'flavor': {'ceph_master': {'keep_minimum': 1, 'days': 0}}}, '__force_dict__': True}
        fake_datetime = fake(utcnow=lambda: self.old, now=self.now)
        monkeypatch.setattr(datetime, 'datetime', fake_datetime)
        session.commit()
        recurring.purge_repos(_now=self.now)
        assert len(Repo.query.all()) == 1


    def test_keeps_new_repo_by_flavor_with_offset_bad_ref_days(self, session, fake, monkeypatch):
        Repo(
            project=Project('nfs-ganesha'),
            ref='next',
            distro='centos',
            distro_version='7',
            flavor='ceph_master',
        )

        conf.purge_rotation = {'nfs-ganesha': {'flavor': {'ceph_master': {'keep_minimum': 1}}, 'ref': {'next': {'days': 0}}}, '__force_dict__': True}
        fake_datetime = fake(utcnow=lambda: self.old, now=self.now)
        monkeypatch.setattr(datetime, 'datetime', fake_datetime)
        session.commit()
        recurring.purge_repos(_now=self.now)
        assert len(Repo.query.all()) == 1

    def test_keeps_new_repo_by_ref_with_days_bad_flavor_offset(self, session, fake, monkeypatch):
        Repo(
            project=Project('nfs-ganesha'),
            ref='next',
            distro='centos',
            distro_version='7',
            flavor='ceph_master',
        )

        conf.purge_rotation = {'nfs-ganesha': {'flavor': {'ceph_master': {'keep_minimum': 0}}, 'ref': {'next': {'days': 70}}}, '__force_dict__': True}
        fake_datetime = fake(utcnow=lambda: self.old, now=self.now)
        monkeypatch.setattr(datetime, 'datetime', fake_datetime)
        session.commit()
        recurring.purge_repos(_now=self.now)
        assert len(Repo.query.all()) == 1


    def test_get_rid_of_new_repo_with_ref_and_flavor(self, session, fake, monkeypatch):
        Repo(
            project=Project('nfs-ganesha'),
            ref='next',
            distro='centos',
            distro_version='7',
            flavor='ceph_master',
        )

        conf.purge_rotation = {'nfs-ganesha': {'flavor': {'ceph_master': {'keep_minimum': 0}}, 'ref': {'next': {'days': 0}}}, '__force_dict__': True}
        fake_datetime = fake(utcnow=lambda: self.old, now=self.now)
        monkeypatch.setattr(datetime, 'datetime', fake_datetime)
        session.commit()
        recurring.purge_repos(_now=self.now)
        assert len(Repo.query.all()) == 0

    def test_get_rid_of_new_repos_without_offset(self, session, fake, monkeypatch):
        Repo(
            project=Project('nfs-ganesha'),
            ref='next',
            distro='centos',
            distro_version='7',
            flavor='ceph_master',
        )

        conf.purge_rotation = {'nfs-ganesha': {'flavor': {'ceph_master': {'days': 0}}, 'ref': {'next': {'days': 0}}}, '__force_dict__': True}
        fake_datetime = fake(utcnow=lambda: self.old, now=self.now)
        monkeypatch.setattr(datetime, 'datetime', fake_datetime)
        session.commit()
        recurring.purge_repos(_now=self.now)
        assert len(Repo.query.all()) == 0


    def test_get_rid_of_new_and_old_repos_without_days(self, session, fake, monkeypatch):
        Repo(
            project=Project('nfs-ganesha'),
            ref='next',
            distro='centos',
            distro_version='7',
            flavor='ceph_master',
        )

        conf.purge_rotation = {'nfs-ganesha': {'flavor': {'ceph_master': {'keep_minimum': 0}}, 'ref': {'next': {'keep_minimum': 0}}}, '__force_dict__': True}
        fake_datetime = fake(utcnow=lambda: self.old, now=self.now)
        monkeypatch.setattr(datetime, 'datetime', fake_datetime)
        session.commit()
        recurring.purge_repos(_now=self.now)
        assert len(Repo.query.all()) == 0

    def test_gets_rid_of_other_repos(self, session, fake, monkeypatch):
        Repo(
            self.p,
            ref='hammer',
            distro='centos',
            distro_version='7',
        )

        conf.purge_rotation = {'ceph': {'ref': {'firefly': {'keep_minimum': 1}}}, '__force_dict__': True}
        fake_datetime = fake(utcnow=lambda: self.old, now=self.now)
        monkeypatch.setattr(datetime, 'datetime', fake_datetime)
        session.commit()
        recurring.purge_repos(_now=self.now)
        assert Repo.query.first().ref == 'firefly'

    def test_gets_rid_of_old_repos_paths(self, session, fake, monkeypatch, tmpdir):
        repo_path = str(tmpdir)
        package = tmpdir.join('ceph-1.0.rpm')
        package.write("101010101010")
        self.repo.path = str(repo_path)
        fake_datetime = fake(utcnow=lambda: self.old, now=self.now)
        monkeypatch.setattr(datetime, 'datetime', fake_datetime)
        session.commit()
        recurring.purge_repos(_now=self.now)
        assert os.path.exists(repo_path) is False

    def test_leaves_newer_repos_behind(self, session, fake, monkeypatch):
        session.commit()
        fake_datetime = fake(utcnow=lambda: self.old, now=self.now)
        monkeypatch.setattr(datetime, 'datetime', fake_datetime)
        session.commit()
        recurring.purge_repos(_now=self.now)
        assert len(Repo.query.all()) == 1

    def test_deletes_related_binaries_as_well(self, session, fake, monkeypatch, tmpdir):
        p = tmpdir.join('binary')
        p.write('contents')
        fake_datetime = fake(utcnow=lambda: self.old, now=self.now)
        monkeypatch.setattr(datetime, 'datetime', fake_datetime)
        Binary(
            'ceph-10.0.0.rpm', self.p, distro='centos',
            distro_version='6',
            arch='i386',
            path=str(p),
            repo=self.repo
        )
        session.commit()
        assert len(Binary.query.all()) == 1
        recurring.purge_repos(_now=self.now)
        assert len(Binary.query.all()) == 0

    def test_ignores_binaries_that_do_not_exist(self, session, fake, monkeypatch, tmpdir):
        p = tmpdir.join('binary')
        p.write_text('contents', encoding='utf-8')
        fake_datetime = fake(utcnow=lambda: self.old, now=self.now)
        monkeypatch.setattr(datetime, 'datetime', fake_datetime)
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
        recurring.purge_repos(_now=self.now)
        assert len(Binary.query.all()) == 0

    def test_if_disabled_it_does_not_purge_binaries(self, session, fake, monkeypatch, tmpdir):
        conf.purge_repos = False
        p = tmpdir.join('binary')
        p.write('contents')
        fake_datetime = fake(utcnow=lambda: self.old, now=self.now)
        monkeypatch.setattr(datetime, 'datetime', fake_datetime)
        Binary(
            'ceph-10.0.0.rpm', self.p, distro='centos',
            distro_version='6',
            arch='i386',
            path=str(p),
            repo=self.repo
        )
        session.commit()
        recurring.purge_repos(_now=self.now)
        assert len(Binary.query.all()) == 1

    def test_does_not_get_rid_of_old_repos(self, session, fake, monkeypatch):
        conf.purge_repos = False
        fake_datetime = fake(utcnow=lambda: self.old, now=self.now)
        monkeypatch.setattr(datetime, 'datetime', fake_datetime)
        session.commit()
        recurring.purge_repos(_now=self.now)
        assert len(Repo.query.all()) == 1


