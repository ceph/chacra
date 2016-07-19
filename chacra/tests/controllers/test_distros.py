from chacra.models import Project, Binary


class TestDistroVersionController(object):

    def test_distro_should_list_unique_versions(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.deb', p, ref='master', sha1="head", distro='ubuntu', distro_version='trusty', arch='i386')
        Binary('ceph-1.0.1.deb', p, ref='master', sha1="head", distro='ubuntu', distro_version='trusty', arch='i386')
        session.commit()
        result = session.app.get('/binaries/ceph/master/head/ubuntu/trusty/')
        assert set(result.json["i386"]) == set([u'ceph-1.0.0.deb', u'ceph-1.0.1.deb'])


class TestDistroController(object):

    def test_list_a_distro_version(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.deb', p, ref='master', sha1="head", distro='ubuntu', distro_version='trusty', arch='i386')
        session.commit()
        result = session.app.get('/binaries/ceph/master/head/ubuntu/')
        assert result.json == {'trusty': ['i386']}

    def test_list_a_distinct_distro_version(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.deb', p, ref='master', sha1="head", distro='ubuntu', distro_version='trusty', arch='i386')
        Binary('ceph-1.0.0.deb', p, ref='firefly', sha1="head", distro='debian', distro_version='wheezy', arch='i386')
        session.commit()
        result = session.app.get(
            '/binaries/ceph/master/head/debian/',
            expect_errors=True)
        assert result.status_int == 404

    def test_list_unkown_ref_for_distro(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.deb', p, ref='master', sha1="head", distro='ubuntu', distro_version='trusty', arch='i386')
        session.commit()
        result = session.app.get('/binaries/ceph/head/BOGUS/ubuntu/', expect_errors=True)
        assert result.status_int == 404

    def test_distro_should_list_unique_versions(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.deb', p, ref='master', sha1="head", distro='ubuntu', distro_version='trusty', arch='i386')
        Binary('ceph-1.0.1.deb', p, ref='master', sha1="head", distro='ubuntu', distro_version='trusty', arch='i386')
        session.commit()
        result = session.app.get('/binaries/ceph/master/head/ubuntu/')
        assert result.json == {'trusty': ['i386']}

    def test_list_a_distro_version_not_found(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.rpm', p, ref='master', sha1="head", distro='centos', distro_version='el6', arch='i386')
        session.commit()
        result = session.app.get('/binaries/ceph/master/head/ubuntu/', expect_errors=True)
        assert result.status_int == 404

    def test_list_a_distinct_distro(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.deb', p, ref='master', sha1="head", distro='ubuntu', distro_version='trusty', arch='i386')
        Binary('ceph-1.0.0.rpm', p, ref='master', sha1="head", distro='centos', distro_version='el6', arch='i386')
        session.commit()
        result = session.app.get('/binaries/ceph/master/head/ubuntu/')
        assert result.json == {'trusty': ['i386']}

    def test_single_distro_should_have_one_item(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.deb', p, ref='master', sha1="head", distro='ubuntu', distro_version='12.04', arch='i386')
        session.commit()
        result = session.app.get('/binaries/ceph/master/head/ubuntu/')
        assert result.status_int == 200
        assert len(result.json) == 1

    def test_refs_should_not_pollute_others(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.deb', p, ref='master', sha1="head", distro='ubuntu', distro_version='precise', arch='i386')
        Binary('ceph-1.0.0.deb', p, ref='jewel', sha1="head", distro='ubuntu', distro_version='xenial', arch='arm64')
        session.commit()
        result = session.app.head('/binaries/ceph/master/head/ubuntu/xenial/arm64/', expect_errors=True)
        assert result.status_int == 404

    def test_distros_should_not_pollute_others(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.deb', p, ref='master', sha1="head", distro='ubuntu', distro_version='precise', arch='i386')
        Binary('ceph-1.0.0.deb', p, ref='jewel', sha1="head", distro='debian', distro_version='xenial', arch='arm64')
        session.commit()
        result = session.app.head('/binaries/ceph/master/head/debian/', expect_errors=True)
        assert result.status_int == 404

    def test_single_distro_should_have_a_name(self, session):
        p = Project('ceph')
        Binary('ceph-1.0.0.deb', p, ref='master', sha1="head", distro='ubuntu', distro_version='12.04', arch='i386')
        session.commit()
        result = session.app.get('/binaries/ceph/master/head/ubuntu/')
        print result
        assert result.json['12.04'] == ['i386']
