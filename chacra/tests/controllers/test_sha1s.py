from chacra.models import Project, Binary


class TestSHA1Controller(object):

    def test_get_index_single_sha1(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.rpm', p, sha1="head", ref='master', distro='centos', distro_version='el6', arch='i386')
        session.commit()
        result = session.app.get('/binaries/ceph/master/head/')
        assert result.json == {'centos': ['el6']}

    def test_get_index_no_sha1(self, session):
        Project('ceph')
        session.commit()
        result = session.app.get('/binaries/ceph/next/sha1/', expect_errors=True)
        assert result.status_int == 404

    def test_get_index_sha1_with_distro(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.rpm', p, sha1="head", ref='master', distro='centos', distro_version='el6', arch='i386')
        session.commit()
        result = session.app.get('/binaries/ceph/master/head/')
        assert result.json['centos'] == ['el6']

    def test_get_index_sha1_with_distros(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.rpm', p, ref='master', sha1="head", distro='centos', distro_version='el6', arch='i386')
        Binary('ceph-1.0.0.deb', p, ref='master', sha1="head", distro='ubuntu', distro_version='trusty', arch='i386')
        session.commit()
        result = session.app.get('/binaries/ceph/master/head/')
        assert set(result.json.keys()) == set(['centos', 'ubuntu'])

    def test_get_sha1_with_distinct_distros(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.rpm', p, ref='master', sha1="head", distro='centos', distro_version='el6', arch='i386')
        # note how we are using a different ref
        Binary('ceph-1.0.0.deb', p, ref='firefly', sha1="head", distro='ubuntu', distro_version='trusty', arch='i386')
        session.commit()
        result = session.app.get('/binaries/ceph/master/head/')
        assert result.json.keys() == ['centos']

    def test_get_distro_with_distinct_distros_different_sha1(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.rpm', p, ref='master', sha1="sha1", distro='centos', distro_version='el6', arch='i386')
        # note how we are using a different ref
        Binary('ceph-1.0.0.deb', p, ref='master', sha1="head", distro='ubuntu', distro_version='trusty', arch='i386')
        session.commit()
        result = session.app.get('/binaries/ceph/master/head/')
        assert result.json.keys() == ['ubuntu']
