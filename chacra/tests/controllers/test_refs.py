from chacra.models import Project, Binary


class TestRefController(object):

    def test_get_index_single_ref(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.rpm', p, ref='main', sha1="head", distro='centos', distro_version='el6', arch='i386')
        session.commit()
        result = session.app.get('/binaries/ceph/main/')
        assert result.json == {'head': ['centos']}

    def test_get_index_no_ref(self, session):
        Project('ceph')
        session.commit()
        result = session.app.get('/binaries/ceph/next/', expect_errors=True)
        assert result.status_int == 404

    def test_get_index_ref_with_sha1(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.rpm', p, ref='main', sha1="head", distro='centos', distro_version='el6', arch='i386')
        session.commit()
        result = session.app.get('/binaries/ceph/main/')
        assert result.json['head'] == ['centos']

    def test_get_index_ref_with_sha1s(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.rpm', p, ref='main', sha1="sha1", distro='centos', distro_version='el6', arch='i386')
        Binary('ceph-1.0.0.deb', p, ref='main', sha1="head", distro='ubuntu', distro_version='trusty', arch='i386')
        session.commit()
        result = session.app.get('/binaries/ceph/main/')
        assert set(result.json.keys()) == set(['head', 'sha1'])

    def test_get_ref_with_distinct_sha1s(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.rpm', p, ref='main', sha1="sha1", distro='centos', distro_version='el6', arch='i386')
        # note how we are using a different ref
        Binary('ceph-1.0.0.deb', p, ref='firefly', sha1="head", distro='ubuntu', distro_version='trusty', arch='i386')
        session.commit()
        result = session.app.get('/binaries/ceph/main/')
        assert list(result.json.keys()) == ['sha1']
