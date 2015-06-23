from chacra.models import Project, Binary


class TestDistroController(object):

    def test_list_a_distro_version(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.deb', p, ref='master', distro='ubuntu', distro_version='trusty', arch='i386')
        session.commit()
        result = session.app.get('/projects/ceph/master/ubuntu/')
        assert result.json == {'trusty': ['i386']}

    def test_distro_should_list_unique_versions(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.deb', p, ref='master', distro='ubuntu', distro_version='trusty', arch='i386')
        Binary('ceph-1.0.1.deb', p, ref='master', distro='ubuntu', distro_version='trusty', arch='i386')
        session.commit()
        result = session.app.get('/projects/ceph/master/ubuntu/')
        assert result.json == {'trusty': ['i386']}

    def test_list_a_distro_version_not_found(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.rpm', p, ref='master', distro='centos', distro_version='el6', arch='i386')
        session.commit()
        result = session.app.get('/projects/ceph/master/ubuntu/', expect_errors=True)
        assert result.status_int == 404

    def test_list_a_distinct_distro(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.deb', p, ref='master', distro='ubuntu', distro_version='trusty', arch='i386')
        Binary('ceph-1.0.0.rpm', p, ref='master', distro='centos', distro_version='el6', arch='i386')
        session.commit()
        result = session.app.get('/projects/ceph/master/ubuntu/')
        assert result.json == {'trusty': ['i386']}

    def test_single_distro_should_have_one_item(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.deb', p, ref='master', distro='ubuntu', distro_version='12.04', arch='i386')
        session.commit()
        result = session.app.get('/projects/ceph/master/ubuntu/')
        assert result.status_int == 200
        assert len(result.json) == 1

    def test_single_distro_should_have_a_name(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.deb', p, ref='master', distro='ubuntu', distro_version='12.04', arch='i386')
        session.commit()
        result = session.app.get('/projects/ceph/master/ubuntu/')
        print result
        assert result.json['12.04'] == ['i386']
