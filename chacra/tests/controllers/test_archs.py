import os
import pecan
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

    def test_single_binary_file_creates_resource(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        result = session.app.post(
            '/projects/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            params={'force': 1},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        assert result.status_int == 201

    def test_new_binary_upload_creates_model_with_path_forced(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)

        session.app.post(
            '/projects/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            params={'force': '1'},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        session.app.post(
            '/projects/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            params={'force': '1'},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        session.app.post(
            '/projects/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            params={'force': '1'},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )

        binary = Binary.get(1)
        assert binary.path.endswith('ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm')

    def test_new_binary_upload_fails_with_existing(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)

        # we do a bunch of requests that do talk to the database
        session.app.post(
            '/projects/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        result = session.app.post(
            '/projects/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')],
            expect_errors=True
        )

        assert result.status_int == 400

    def test_single_binary_file_uploaded_twice_gets_updated(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        result = session.app.post(
            '/projects/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        result = session.app.post(
            '/projects/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        assert result.status_int == 200

    def test_single_binary_file_should_create_all_url(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        session.app.post(
            '/projects/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        session.app.post(
            '/projects/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'something changed')]
        )
        contents = open(os.path.join(pecan.conf.binary_root, 'ceph-9.0.0-0.el6.x86_64.rpm')).read()
        assert contents == 'something changed'
