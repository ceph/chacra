from chacra.models import Project, Binary


class TestFlavorsController(object):

    def test_list_single_flavor(self, session):
        project = Project('ceph')
        Binary(
            'ceph-1.0.0.rpm',
            project,
            ref='giant',
            sha1="head",
            distro='centos',
            distro_version='el6',
            arch='x86_64',
            flavor='tcmalloc'
        )
        session.commit()
        result = session.app.get(
            '/binaries/ceph/giant/head/centos/el6/x86_64/flavors/',
        )
        assert result.json['tcmalloc'] == ['ceph-1.0.0.rpm']

    def test_list_unique_flavor(self, session):
        project = Project('ceph')
        Binary(
            'ceph-1.0.0.rpm',
            project,
            ref='giant',
            sha1="head",
            distro='centos',
            distro_version='el6',
            arch='x86_64',
            flavor='tcmalloc'
        )
        Binary(
            'ceph-1.0.0.rpm',
            project,
            ref='giant',
            sha1="head",
            distro='centos',
            distro_version='el7',
            arch='x86_64',
            flavor='tcmalloc'
        )
        session.commit()
        result = session.app.get(
            '/binaries/ceph/giant/head/centos/el6/x86_64/flavors/',
        )
        assert result.json['tcmalloc'] == ['ceph-1.0.0.rpm']

    def test_list_one_flavor(self, session):
        project = Project('ceph')
        Binary(
            'ceph-1.0.0.rpm',
            project,
            ref='giant',
            sha1="head",
            distro='centos',
            distro_version='el6',
            arch='x86_64',
            flavor='tcmalloc'
        )
        Binary(
            'ceph-1.0.0.rpm',
            project,
            ref='giant',
            sha1="head",
            distro='centos',
            distro_version='el7',
            arch='x86_64',
            flavor='default'
        )
        session.commit()
        result = session.app.get(
            '/binaries/ceph/giant/head/centos/el6/x86_64/flavors/',
        )
        # default flavor is for a different distro_version in this case
        # and should not show up
        assert result.json.keys() == ['tcmalloc']


class TestFlavorController(object):

    def test_list_flavor_one_binary(self, session):
        project = Project('ceph')
        Binary(
            'ceph-1.0.0.rpm',
            project,
            ref='giant',
            sha1="head",
            distro='centos',
            distro_version='el6',
            arch='x86_64',
            flavor='tcmalloc'
        )
        session.commit()
        result = session.app.get('/binaries/ceph/giant/head/centos/el6/x86_64/flavors/tcmalloc/')
        assert result.json['ceph-1.0.0.rpm']

    def test_list_flavor_one_binary_on_arch(self, session):
        project = Project('ceph')
        Binary(
            'ceph-1.0.0.rpm',
            project,
            ref='giant',
            sha1="head",
            distro='centos',
            distro_version='el6',
            arch='x86_64',
            flavor='tcmalloc'
        )
        session.commit()
        result = session.app.get('/binaries/ceph/giant/head/centos/el6/x86_64/')
        assert result.json['ceph-1.0.0.rpm']

    def test_list_default_flavor_one_binary_on_arch(self, session):
        project = Project('ceph')
        Binary(
            'ceph-1.0.0.rpm',
            project,
            ref='giant',
            sha1="head",
            distro='centos',
            distro_version='el6',
            arch='x86_64',
            flavor='tcmalloc'
        )
        session.commit()
        result = session.app.get('/binaries/ceph/giant/head/centos/el6/x86_64/')
        assert result.json['ceph-1.0.0.rpm']

    def test_list_default_flavor_one_binary(self, session):
        # note how 'flavor' is not specified
        project = Project('ceph')
        Binary(
            'ceph-1.0.0.rpm',
            project,
            ref='giant',
            sha1="head",
            distro='centos',
            distro_version='el6',
            arch='x86_64',
        )
        session.commit()
        result = session.app.get('/binaries/ceph/giant/head/centos/el6/x86_64/flavors/default/')
        assert result.json['ceph-1.0.0.rpm']

    def test_flavor_not_found_with_head(self, session):
        project = Project('ceph')
        Binary(
            'ceph-1.0.0.rpm',
            project,
            ref='giant',
            sha1="head",
            distro='centos',
            distro_version='el6',
            arch='x86_64'
        )
        session.commit()
        result = session.app.head(
            '/binaries/ceph/giant/head/centos/el7/x86_64/flavors/default/', expect_errors=True)
        assert result.status_int == 404

    def test_single_flavor_should_have_one_item(self, session):
        p = Project('ceph')
        Binary(
            'ceph-9.0.0-0.el6.x86_64.rpm',
            p,
            ref='giant',
            sha1="head",
            distro='centos',
            distro_version='el6',
            arch='x86_64'
        )
        session.commit()
        result = session.app.get('/binaries/ceph/giant/head/centos/el6/x86_64/flavors/default/')
        assert result.status_int == 200
        assert len(result.json) == 1

    def test_single_binary_file_creates_resource(self, session, tmpdir):
        import pecan
        pecan.conf.binary_root = str(tmpdir)
        result = session.app.post(
            '/binaries/ceph/giant/head/ceph/el6/x86_64/flavors/frufru/',
            params={'force': 1},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        assert result.status_int == 201


