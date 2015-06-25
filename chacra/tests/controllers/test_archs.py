from chacra.models import Project, Binary


class TestArchController(object):

    def test_list_arch_no_binaries(self, session):
        Project('ceph')
        session.commit()
        result = session.app.get('/projects/ceph/giant/centos/el6/x86_64/', expect_errors=True)
        assert result.status_int == 404

    def test_list_arch_one_binary(self, session):
        project = Project('ceph')
        Binary('ceph-1.0.0.rpm', project, ref='giant', distro='centos', distro_version='el6', arch='x86_64')
        session.commit()
        result = session.app.get('/projects/ceph/giant/centos/el6/x86_64/')
        assert result.json['ceph-1.0.0.rpm']

    def test_single_arch_should_have_one_item(self, session):
        p = Project('ceph')
        Binary('ceph-9.0.0-0.el6.x86_64.rpm', p, ref='giant', distro='centos', distro_version='el6', arch='x86_64')
        session.commit()
        result = session.app.get('/projects/ceph/giant/centos/el6/x86_64/')
        assert result.status_int == 200
        assert len(result.json) == 1

    def test_single_binary_should_not_be_signed(self, session):
        p = Project('ceph')
        Binary('ceph-9.0.0-0.el6.x86_64.rpm', p, ref='giant', distro='centos', distro_version='el6', arch='x86_64')
        session.commit()
        result = session.app.get('/projects/ceph/giant/centos/el6/x86_64/')
        assert result.json['ceph-9.0.0-0.el6.x86_64.rpm']['signed'] is False

    def test_single_binary_should_have_default_size_cero(self, session):
        p = Project('ceph')
        Binary('ceph-9.0.0-0.el6.x86_64.rpm', p, ref='giant', distro='centos', distro_version='el6', arch='x86_64')
        session.commit()
        result = session.app.get('/projects/ceph/giant/centos/el6/x86_64/')
        assert result.json['ceph-9.0.0-0.el6.x86_64.rpm']['size'] == 0

    def test_single_binary_should_create_all_url(self, session):
        session.app.post_json(
            '/projects/ceph/giant/ceph/el6/x86_64/',
            params=dict(name='ceph-9.0.0-0.el6.x86_64.rpm'))
        result = session.app.get('/projects/ceph/giant/ceph/el6/x86_64/')
        result.json['ceph-9.0.0-0.el6.x86_64.rpm']['name'] == 'ceph-9.0.0-0.el6.x86_64.rpm'

    def test_multiple_binaries(self, session):
        session.app.post_json(
            '/projects/ceph/giant/ceph/el6/x86_64/',
            params=dict(name='ceph-9.0.0-0.el6.x86_64.rpm'))
        session.app.post_json(
            '/projects/ceph/giant/ceph/el6/x86_64/',
            params=dict(name='ceph-9.1.0-0.el6.x86_64.rpm'))
        session.app.post_json(
            '/projects/ceph/giant/ceph/el6/x86_64/',
            params=dict(name='ceph-9.0.2-0.el6.x86_64.rpm'))
        result = session.app.get('/projects/ceph/giant/ceph/el6/x86_64/')
        assert len(result.json.keys()) == 3
        result.json['ceph-9.0.0-0.el6.x86_64.rpm']['name'] == 'ceph-9.0.0-0.el6.x86_64.rpm'

    def test_multiple_binaries_in_same_arch_different_versions(self, session):
        # post same binary to el6 and el7 and same x86_64 arch
        session.app.post_json(
            '/projects/ceph/giant/ceph/el6/x86_64/',
            params=dict(name='ceph-9.0.0-0.el6.x86_64.rpm'))
        session.app.post_json(
            '/projects/ceph/giant/ceph/el7/x86_64/',
            params=dict(name='ceph-9.1.0-0.el6.x86_64.rpm'))
        el6 = session.app.get('/projects/ceph/giant/ceph/el6/x86_64/')
        el7 = session.app.get('/projects/ceph/giant/ceph/el7/x86_64/')
        assert len(el6.json.keys()) == 1
        assert len(el7.json.keys()) == 1

    def test_multiple_same_binaries_in_same_arch_different_versions(self, session):
        # post same binary to el6 and el7 and same x86_64 arch
        session.app.post_json(
            '/projects/ceph/giant/ceph/el6/x86_64/',
            params=dict(name='ceph-9.0.0-0.el6.x86_64.rpm'))
        session.app.post_json(
            '/projects/ceph/giant/ceph/el7/x86_64/',
            params=dict(name='ceph-9.0.0-0.el6.x86_64.rpm'))
        result = session.app.get('/projects/ceph/giant/ceph/el6/x86_64/')
        assert len(result.json.keys()) == 1
        result.json['ceph-9.0.0-0.el6.x86_64.rpm']['name'] == 'ceph-9.0.0-0.el6.x86_64.rpm'

    def test_set_the_path_on_binary(self, session):
        session.app.post_json(
            '/projects/ceph/giant/ceph/el6/x86_64/',
            params=dict(
                name='ceph-9.0.0-0.el6.x86_64.rpm',
                path='/'))
        result = session.app.get('/projects/ceph/giant/ceph/el6/x86_64/')
        result.json['ceph-9.0.0-0.el6.x86_64.rpm']['path'] == '/'

    def test_do_not_allow_overwriting(self, session):
        session.app.post_json(
            '/projects/ceph/giant/centos/el6/x86_64/',
            params=dict(
                name='ceph-9.0.0-0.el6.x86_64.rpm',
                path='/'))
        result = session.app.post_json(
            '/projects/ceph/giant/centos/el6/x86_64/',
            params=dict(
                name='ceph-9.0.0-0.el6.x86_64.rpm',
                path='/'),
            expect_errors=True)

        assert result.status_int == 400
        assert result.json['message'] == 'file already exists and "force" flag was not used'

    def test_allow_overwriting_with_flag(self, session):
        session.app.post_json(
            '/projects/ceph/giant/centos/el6/x86_64/',
            params=dict(
                name='ceph-9.0.0-0.el6.x86_64.rpm',
                path='/'))
        session.app.post_json(
            '/projects/ceph/giant/centos/el6/x86_64/',
            params=dict(
                name='ceph-9.0.0-0.el6.x86_64.rpm',
                path='/other',
                force=True),
            )
        result = session.app.get('/projects/ceph/giant/centos/el6/x86_64/')
        assert result.json['ceph-9.0.0-0.el6.x86_64.rpm']['path'] == '/other'

    def test_binary_with_path_should_get_size_computed(self, session, tmpdir):
        import pecan, os
        pecan.conf.binary_root = str(tmpdir)
        path = os.path.join(pecan.conf.binary_root, 'ceph-9.0.0-0.el6.x86_64.rpm')
        # fake the file contents, because we assume it already exists:
        with open(path, 'w') as f:
            f.write('existing binary')
        session.app.post_json(
            '/projects/ceph/giant/ceph/el6/x86_64/',
            params=dict(name='ceph-9.0.0-0.el6.x86_64.rpm', path=path))
        result = session.app.get('/projects/ceph/giant/ceph/el6/x86_64/')
        assert result.json['ceph-9.0.0-0.el6.x86_64.rpm']['size'] == 15

