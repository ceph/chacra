from chacra.models import Binary, Project, Repo


class TestBinaryModification(object):

    def setup(self):
        self.p = Project('ceph')

    def test_created_equals_modified_first_time_around(self, session):
        binary = Binary(
            'ceph-1.0.rpm',
            self.p,
            distro='centos',
            distro_version='7',
            arch='x86_64',
            )
        session.commit()
        assert binary.created.timetuple() == binary.modified.timetuple()

    def test_modified_gets_updated(self, session):
        binary = Binary(
            'ceph-1.0.rpm',
            self.p,
            distro='centos',
            distro_version='7',
            arch='x86_64',
            )
        session.commit()
        initial_modified = binary.modified.time()
        binary.ref = 'master'
        session.commit()
        binary = Binary.get(1)

        assert initial_modified < binary.modified.time()

    def test_modified_is_older_than_created(self, session):
        binary = Binary(
            'ceph-1.0.rpm',
            self.p,
            distro='centos',
            distro_version='7',
            arch='x86_64',
            )
        session.commit()
        initial_created = binary.created.time()
        binary.ref = 'master'
        session.commit()
        binary = Binary.get(1)

        assert initial_created < binary.modified.time()

    def test_binary_uses_explicit_repo(self, session):
        repo = Repo(self.p, 'firefly', 'centos', '7')
        binary = Binary(
            'ceph-1.0.rpm',
            self.p,
            distro='centos',
            distro_version='7',
            arch='x86_64',
            repo=repo,
            )
        session.commit()
        binary = Binary.get(1)
        assert binary.repo.ref == 'firefly'
        assert binary.repo.distro_version == '7'

    def test_binary_create_repo_object(self, session):
        binary = Binary(
            'ceph-1.0.rpm',
            self.p,
            ref='firefly',
            distro='centos',
            distro_version='7',
            arch='x86_64',
            )
        session.commit()
        binary = Binary.get(1)
        assert binary.repo.ref == 'firefly'
        assert binary.repo.distro_version == '7'

    def test_binary_reuse_repo_object(self, session):
        Repo(self.p, 'hammer', 'centos', '7')
        session.commit()
        binary = Binary(
            'ceph-1.0.rpm',
            self.p,
            ref='hammer',
            distro='centos',
            distro_version='7',
            arch='x86_64',
            )
        session.commit()
        binary = Binary.get(1)
        assert binary.repo.ref == 'hammer'
        assert binary.repo.distro_version == '7'

    def test_binary_sets_repo_type(self, session):
        repo = Repo(self.p, 'hammer', 'centos', '7')
        session.commit()
        Binary(
            'ceph-1.0.rpm',
            self.p,
            ref='hammer',
            distro='centos',
            distro_version='7',
            arch='x86_64',
            )
        session.commit()
        repo = Repo.get(1)
        assert repo.type == 'rpm'

    def test_binary_type_for_changes(self, session):
        repo = Repo(self.p, 'hammer', 'debian', 'wheezy')
        Binary(
            'ceph-1.0.changes',
            self.p,
            ref='hammer',
            distro='debian',
            distro_version='wheezy',
            arch='amd64',
            )
        assert repo.type == 'deb'

    def test_binary_type_for_dsc(self, session):
        repo = Repo(self.p, 'hammer', 'debian', 'wheezy')
        Binary(
            'ceph-1.0.dsc',
            self.p,
            ref='hammer',
            distro='debian',
            distro_version='wheezy',
            arch='amd64',
            )
        assert repo.type == 'deb'

    def test_binary_type_for_tar(self, session):
        repo = Repo(self.p, 'hammer', 'debian', 'wheezy')
        Binary(
            'ceph-1.0.tar.gz',
            self.p,
            ref='hammer',
            distro='debian',
            distro_version='wheezy',
            arch='amd64',
            )
        assert repo.type == 'deb'


class TestGenericBinaries(object):

    def setup(self):
        self.p = Project('ceph')

    def test_binary_is_generic(self, session):
        binary = Binary(
            'ceph-1.0.deb',
            self.p,
            ref='hammer',
            distro='debian',
            distro_version='generic',
            arch='amd64',
            )
        assert binary.repo.is_generic is True

    def test_binary_is_not_generic(self, session):
        binary = Binary(
            'ceph-1.0.deb',
            self.p,
            ref='hammer',
            distro='debian',
            distro_version='wheezy',
            arch='amd64',
            )
        assert binary.repo.is_generic is False
