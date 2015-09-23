import os
import pecan
from chacra.models import Binary
from chacra.tests import util


class TestBinaryUniqueness(object):
    # ensure that there is no pollution from other projects or architectures

    def test_two_projects_different_archs(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        session.app.post(
            '/projects/ceph/giant/centos/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )

        session.app.post(
            '/projects/ceph-deploy/master/centos/el6/i386/ceph-deploy-1.0.0-0.el6.i386.rpm/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )

        # get archs for ceph-deploy
        result = session.app.get(
            '/projects/ceph-deploy/master/centos/el6/',
        )

        assert result.json['i386'] == ['ceph-deploy-1.0.0-0.el6.i386.rpm']


class TestBinaryController(object):

    def test_single_binary_file_creates_resource(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        result = session.app.post(
            '/projects/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            params={'force': 1},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        assert result.status_int == 201

    def test_auth_fails(self, session):
        result = session.app.post(
            '/projects/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')],
            headers={'Authorization': util.make_credentials(correct=False)},
            expect_errors=True
        )
        assert result.status_int == 401

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

    def test_posting_twice_requires_force_flag(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        result = session.app.post(
            '/projects/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        result = session.app.post(
            '/projects/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            params={'force': True},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        assert result.status_int == 200

    def test_posting_twice_updates_the_binary(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        session.app.post(
            '/projects/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        session.app.post(
            '/projects/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            params={'force': True},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'something changed')]
        )

        destination = os.path.join(
            pecan.conf.binary_root,
            'ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm'
        )

        contents = open(destination).read()
        assert contents == 'something changed'

    def test_binary_gets_size_computed(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        result = session.app.post(
            '/projects/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        response = session.app.get('/projects/ceph/giant/ceph/el6/x86_64/').json
        result = response['ceph-9.0.0-0.el6.x86_64.rpm']['size']
        assert result == 13

    def test_binary_gets_checksum_computed(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        result = session.app.post(
            '/projects/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        response = session.app.get('/projects/ceph/giant/ceph/el6/x86_64/').json
        result = response['ceph-9.0.0-0.el6.x86_64.rpm']['checksum']
        assert len(result) == 128
        assert result.startswith('318b')

    def test_binary_gets_checksum_computed_when_updated(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        result = session.app.post(
            '/projects/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        response = session.app.get('/projects/ceph/giant/ceph/el6/x86_64/').json
        result = response['ceph-9.0.0-0.el6.x86_64.rpm']['checksum']
        assert result.startswith('318b')
        session.app.post(
            '/projects/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            params={'force': True},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'something changed')]
        )
        response = session.app.get('/projects/ceph/giant/ceph/el6/x86_64/').json
        result = response['ceph-9.0.0-0.el6.x86_64.rpm']['checksum']
        assert result.startswith('a5725e467')
