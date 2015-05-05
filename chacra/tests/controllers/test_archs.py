from chacra.models import Project, Distro, DistroVersion, DistroArch, Binary, Ref


class TestArchController(object):

    def test_list_arch_no_binaries(self, session):
        project = Project('ceph')
        ref = Ref('giant', project)
        distro = Distro('centos', ref)
        version = DistroVersion('el6', distro)
        DistroArch('x86_64', version)
        session.commit()
        result = session.app.get('/projects/ceph/giant/centos/el6/x86_64/')
        assert result.json == {}

    def test_single_arch_should_have_one_item(self, session):
        project = Project('ceph')
        ref = Ref('giant', project)
        distro = Distro('centos', ref)
        version = DistroVersion('el6', distro)
        arch = DistroArch('x86_64', version)
        Binary('ceph-9.0.0-0.el6.x86_64.rpm', arch)
        session.commit()
        result = session.app.get('/projects/ceph/giant/centos/el6/x86_64/')
        assert result.status_int == 200
        assert len(result.json) == 1

    def test_single_binary_should_not_be_signed(self, session):
        project = Project('ceph')
        ref = Ref('giant', project)
        distro = Distro('centos', ref)
        version = DistroVersion('el6', distro)
        arch = DistroArch('x86_64', version)
        Binary('ceph-9.0.0-0.el6.x86_64.rpm', arch)
        session.commit()
        result = session.app.get('/projects/ceph/giant/centos/el6/x86_64/')
        assert result.json['ceph-9.0.0-0.el6.x86_64.rpm']['signed'] is False

    def test_single_binary_should_have_default_size_cero(self, session):
        project = Project('ceph')
        ref = Ref('giant', project)
        distro = Distro('centos', ref)
        version = DistroVersion('el6', distro)
        arch = DistroArch('x86_64', version)
        Binary('ceph-9.0.0-0.el6.x86_64.rpm', arch)
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
                '/projects/ceph/giant/ceph/el6/x86_64/',
                params=dict(
                    name='ceph-9.0.0-0.el6.x86_64.rpm',
                    path='/'))
        session.app.post_json(
                '/projects/ceph/giant/ceph/el6/x86_64/',
                params=dict(
                    name='ceph-9.0.0-0.el6.x86_64.rpm',
                    path='/other',
                    force=True),
                )
        result = session.app.get('/projects/ceph/giant/ceph/el6/x86_64/')
        assert result.json['ceph-9.0.0-0.el6.x86_64.rpm']['path'] == '/other'
