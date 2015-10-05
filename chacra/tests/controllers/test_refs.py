from chacra.models import Project, Binary


class TestRefController(object):

    def test_get_index_single_ref(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.rpm', p, ref='master', distro='centos', distro_version='el6', arch='i386')
        session.commit()
        result = session.app.get('/binaries/ceph/master/')
        assert result.json == {'centos': ['el6']}

    def test_get_index_no_ref(self, session):
        Project('ceph')
        session.commit()
        result = session.app.get('/binaries/ceph/next/', expect_errors=True)
        assert result.status_int == 404

    def test_get_index_ref_with_distro(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.rpm', p, ref='master', distro='centos', distro_version='el6', arch='i386')
        session.commit()
        result = session.app.get('/binaries/ceph/master/')
        assert result.json['centos'] == ['el6']

    def test_get_index_ref_with_distros(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.rpm', p, ref='master', distro='centos', distro_version='el6', arch='i386')
        Binary('ceph-1.0.0.deb', p, ref='master', distro='ubuntu', distro_version='trusty', arch='i386')
        session.commit()
        result = session.app.get('/binaries/ceph/master/')
        assert result.json.keys() == ['centos', 'ubuntu']
