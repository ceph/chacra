from chacra.models import Binary, Project


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
