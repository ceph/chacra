from chacra.models import Project, Distro, DistroVersion, DistroArch, Binary


class TestArchController(object):

    def test_list_arch_no_binaries(self, session):
        project = Project('ceph')
        distro = Distro('centos', project)
        version = DistroVersion('el6', distro)
        DistroArch('x86_64', version)
        session.commit()
        result = session.app.get('/projects/ceph/centos/el6/x86_64/')
        assert result.json == {}

    def test_single_arch_should_have_one_item(self, session):
        project = Project('ceph')
        distro = Distro('centos', project)
        version = DistroVersion('el6', distro)
        arch = DistroArch('x86_64', version)
        Binary('ceph-9.0.0-0.el6.x86_64.rpm', arch)
        session.commit()
        result = session.app.get('/projects/ceph/centos/el6/x86_64/')
        assert result.status_int == 200
        assert len(result.json) == 1

    def test_single_binary_should_not_be_signed(self, session):
        project = Project('ceph')
        distro = Distro('centos', project)
        version = DistroVersion('el6', distro)
        arch = DistroArch('x86_64', version)
        Binary('ceph-9.0.0-0.el6.x86_64.rpm', arch)
        session.commit()
        result = session.app.get('/projects/ceph/centos/el6/x86_64/')
        assert result.json['ceph-9.0.0-0.el6.x86_64.rpm']['signed'] is False

    def test_single_binary_should_have_default_size_cero(self, session):
        project = Project('ceph')
        distro = Distro('centos', project)
        version = DistroVersion('el6', distro)
        arch = DistroArch('x86_64', version)
        Binary('ceph-9.0.0-0.el6.x86_64.rpm', arch)
        session.commit()
        result = session.app.get('/projects/ceph/centos/el6/x86_64/')
        assert result.json['ceph-9.0.0-0.el6.x86_64.rpm']['size'] == 0

    def test_single_binary_should_create_all_url(self, session):
        session.app.post_json(
                '/projects/ceph/centos/el6/x86_64/',
                params=dict(name='ceph-9.0.0-0.el6.x86_64.rpm'))
        result = session.app.get('/projects/ceph/centos/el6/x86_64/')
        result.json['ceph-9.0.0-0.el6.x86_64.rpm']['name'] == 'ceph-9.0.0-0.el6.x86_64.rpm'

    def test_set_the_path_on_binary(self, session):
        session.app.post_json(
                '/projects/ceph/centos/el6/x86_64/',
                params=dict(
                    name='ceph-9.0.0-0.el6.x86_64.rpm',
                    path='/'))
        result = session.app.get('/projects/ceph/centos/el6/x86_64/')
        result.json['ceph-9.0.0-0.el6.x86_64.rpm']['path'] == '/'

