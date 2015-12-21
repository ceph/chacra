import os
import pecan

from chacra.models import Binary, Project, Repo
from chacra.tests import util


class TestBinaryUniqueness(object):
    # ensure that there is no pollution from other projects or architectures

    def test_two_projects_different_archs(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        session.app.post(
            '/binaries/ceph/giant/centos/el6/x86_64/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )

        session.app.post(
            '/binaries/ceph-deploy/master/centos/el6/i386/',
            upload_files=[('file', 'ceph-deploy-1.0.0-0.el6.i386.rpm', 'hello tharrrr')]
        )

        # get archs for ceph-deploy
        result = session.app.get(
            '/binaries/ceph-deploy/master/centos/el6/',
        )

        assert result.json['i386'] == ['ceph-deploy-1.0.0-0.el6.i386.rpm']


class TestBinaryController(object):

    def test_single_binary_file_creates_resource(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        result = session.app.post(
            '/binaries/ceph/giant/ceph/el6/x86_64/',
            params={'force': 1},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        assert result.status_int == 201

    def test_put_is_not_allowed(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        session.app.post(
            '/binaries/ceph/giant/ceph/el6/x86_64/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        result = session.app.put(
            '/binaries/ceph/giant/ceph/el6/x86_64/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')],
            expect_errors=True,
        )
        assert result.status_int == 405

    def test_archs_is_not_found(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        # post to a different distro but same arch
        result = session.app.post(
            '/binaries/ceph/giant/ceph/el7/x86_64/',
            params={'force': 1},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        result = session.app.get(
            '/binaries/ceph/giant/ceph/el6/x86_64/',
            expect_errors=True
        )
        assert result.status_int == 404

    def test_single_binary_file_can_be_downloaded(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        session.app.post(
            '/binaries/ceph/giant/ceph/el6/x86_64/',
            params={'force': 1},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        result = session.app.get('/binaries/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/')
        assert result.status_int == 200

    def test_single_binary_file_can_be_deleted(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        session.app.post(
            '/binaries/ceph/giant/ceph/el6/x86_64/',
            params={'force': 1},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        result = session.app.get('/binaries/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/')
        assert result.status_int == 200
        result = session.app.delete('/binaries/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/')
        assert result.status_int == 204
        result = session.app.get('/binaries/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/', expect_errors=True)
        assert result.status_int == 404

    def test_binary_file_can_not_delete_binary_file(self, session, tmpdir):
        p = Project("ceph")
        Binary(
            "ceph-9.0.0-0.el6.x86_64.rpm",
            p,
            distro="ceph",
            distro_version="el6",
            ref="giant",
            arch="x86_64",
        )
        result = session.app.delete('/binaries/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/', expect_errors=True)
        assert result.status_int == 500

    def test_delete_missing_binary_file(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        result = session.app.get('/binaries/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/', expect_errors=True)
        assert result.status_int == 404

    def test_binary_file_deleted_removes_project(self, session, tmpdir):
        # if a project has no binaries related to it after binary deletion, it is deleted as well
        pecan.conf.binary_root = str(tmpdir)
        session.app.post(
            '/binaries/ceph/giant/ceph/el6/x86_64/',
            params={'force': 1},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        result = session.app.delete('/binaries/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/')
        assert result.status_int == 204
        p = Project.get(1)
        assert not p

    def test_binary_file_deleted_project_exists(self, session, tmpdir):
        # if a project has binaries related to it after binary deletion, it will still exist
        pecan.conf.binary_root = str(tmpdir)
        session.app.post(
            '/binaries/ceph/giant/ceph/el6/x86_64/',
            params={'force': 1},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        session.app.post(
            '/binaries/ceph/giant/ceph/el7/x86_64/',
            params={'force': 1},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        result = session.app.delete('/binaries/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/')
        assert result.status_int == 204
        p = Project.get(1)
        assert p.name == "ceph"

    def test_binary_file_deleted_removes_repo(self, session, tmpdir):
        # if a repo has no binaries related to it after binary deletion, it is deleted as well
        pecan.conf.binary_root = str(tmpdir)
        session.app.post(
            '/binaries/ceph/giant/ceph/el6/x86_64/',
            params={'force': 1},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        repo = Repo.get(1)
        assert repo
        result = session.app.delete('/binaries/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/')
        assert result.status_int == 204
        repo = Repo.get(1)
        assert not repo

    def test_binary_file_deleted_repo_exists(self, session, tmpdir):
        # if a repo has binaries related to it after binary deletion, it will still exist
        pecan.conf.binary_root = str(tmpdir)
        session.app.post(
            '/binaries/ceph/giant/ceph/el6/x86_64/',
            params={'force': 1},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        session.app.post(
            '/binaries/ceph/giant/ceph/el6/x86_64/',
            params={'force': 1},
            upload_files=[('file', 'ceph-9.1.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        repo = Repo.get(1)
        assert repo
        result = session.app.delete('/binaries/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/')
        assert result.status_int == 204
        repo = Repo.get(1)
        assert repo.needs_update

    def test_auth_fails(self, session):
        result = session.app.post(
            '/binaries/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')],
            headers={'Authorization': util.make_credentials(correct=False)},
            expect_errors=True
        )
        assert result.status_int == 401

    def test_new_binary_upload_creates_model_with_path_forced(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)

        session.app.post(
            '/binaries/ceph/giant/ceph/el6/x86_64/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        session.app.put(
            '/binaries/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        session.app.put(
            '/binaries/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )

        binary = Binary.get(1)
        assert binary.path.endswith('ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm')

    def test_new_binary_upload_fails_with_existing(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)

        # we do a bunch of requests that do talk to the database
        session.app.post(
            '/binaries/ceph/giant/ceph/el6/x86_64/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        result = session.app.post(
            '/binaries/ceph/giant/ceph/el6/x86_64/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')],
            expect_errors=True
        )

        assert result.status_int == 400

    def test_posting_twice__different_distro_ver_not_requires_force_flag(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        result = session.app.post(
            '/binaries/ceph/giant/ceph/el7/x86_64/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        result = session.app.post(
            '/binaries/ceph/giant/ceph/el6/x86_64/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        assert result.status_int == 201

    def test_posting_twice_updates_the_binary(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        session.app.post(
            '/binaries/ceph/giant/ceph/el6/x86_64/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        session.app.put(
            '/binaries/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
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
            '/binaries/ceph/giant/ceph/el6/x86_64/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        response = session.app.get('/binaries/ceph/giant/ceph/el6/x86_64/').json
        result = response['ceph-9.0.0-0.el6.x86_64.rpm']['size']
        assert result == 13

    def test_binary_gets_checksum_computed(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        result = session.app.post(
            '/binaries/ceph/giant/ceph/el6/x86_64/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        response = session.app.get('/binaries/ceph/giant/ceph/el6/x86_64/').json
        result = response['ceph-9.0.0-0.el6.x86_64.rpm']['checksum']
        assert len(result) == 128
        assert result.startswith('318b')

    def test_binary_gets_checksum_computed_when_updated(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        result = session.app.post(
            '/binaries/ceph/giant/ceph/el6/x86_64/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        response = session.app.get('/binaries/ceph/giant/ceph/el6/x86_64/').json
        result = response['ceph-9.0.0-0.el6.x86_64.rpm']['checksum']
        assert result.startswith('318b')
        session.app.put(
            '/binaries/ceph/giant/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            params={'force': True},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'something changed')]
        )
        response = session.app.get('/binaries/ceph/giant/ceph/el6/x86_64/').json
        result = response['ceph-9.0.0-0.el6.x86_64.rpm']['checksum']
        assert result.startswith('a5725e467')

    def test_head_requests_are_allowed(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        session.app.post(
            '/binaries/ceph/giant/ceph/el6/x86_64/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        response = session.app.head('/binaries/ceph/giant/ceph/el6/x86_64/')
        assert response.status_int == 200


class TestRelatedProjects(object):

    def test_marks_nonexsitent_related_project(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        pecan.conf.repos = {
            'ceph': {
                'all': {'ceph-deploy': ['master']}
            },
            '__force_dict__': True,
        }
        session.app.post(
            '/binaries/ceph-deploy/master/centos/6/x86_64/',
            upload_files=[('file', 'ceph-deploy_9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        project = Project.filter_by(name='ceph').first()
        # should've create the ceph project because it didn't exist
        assert project is not None
        repo = Repo.filter_by(project=project).first()
        assert repo.needs_update is True

    def test_marks_existing_related_project(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        pecan.conf.repos = {
            'ceph': {
                'all': {'ceph-deploy': ['master']}
            },
            '__force_dict__': True,
        }
        Project(name='ceph')
        session.commit()
        session.app.post(
            '/binaries/ceph-deploy/master/centos/6/x86_64/',
            upload_files=[('file', 'ceph-deploy_9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        project = Project.filter_by(name='ceph').first()
        assert project is not None
        repo = Repo.filter_by(project=project).first()
        assert repo.needs_update is True

    def test_marks_multiple_projects(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        pecan.conf.repos = {
            'ceph': {
                'all': {'ceph-deploy': ['master']},
            },
            'rhcs': {
                'all': {'ceph-deploy': ['master']},
            },
            '__force_dict__': True,
        }
        session.commit()
        session.app.post(
            '/binaries/ceph-deploy/master/centos/6/x86_64/',
            upload_files=[('file', 'ceph-deploy_9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        ceph_project = Project.filter_by(name='ceph').first()
        rhcs_project = Project.filter_by(name='rhcs').first()
        assert Repo.filter_by(project=ceph_project).first().needs_update is True
        assert Repo.filter_by(project=rhcs_project).first().needs_update is True

    def test_marks_nonexsitent_related_project_type(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        pecan.conf.repos = {
            'ceph': {
                'all': {'ceph-deploy': ['master']}
            },
            '__force_dict__': True,
        }
        session.app.post(
            '/binaries/ceph-deploy/master/centos/6/x86_64/',
            upload_files=[('file', 'ceph-deploy_9.0.0-0.el6.x86_64.rpm', 'hello tharrrr')]
        )
        project = Project.filter_by(name='ceph').first()
        repo = Repo.filter_by(project=project).first()
        assert repo.type == 'rpm'
