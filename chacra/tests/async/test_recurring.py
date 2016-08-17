import datetime
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

    def test_gets_rid_of_old_repos(self, session, fake, monkeypatch):
        fake_datetime = fake(utcnow=lambda: self.old, now=self.now)
        monkeypatch.setattr(datetime, 'datetime', fake_datetime)
        session.commit()
        recurring.purge_repos(_now=self.now)
        assert Repo.query.all() == []

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
