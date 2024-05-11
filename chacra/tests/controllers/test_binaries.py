import os
import pecan
import pytest

from chacra.models import Binary, Project, Repo
from chacra.tests import util
from chacra.compat import b_


class TestBinaryUniqueness(object):
    # ensure that there is no pollution from other projects or architectures

    def test_two_projects_different_archs(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        session.app.post(
            '/binaries/ceph/giant/head/centos/el6/x86_64/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )

        session.app.post(
            '/binaries/ceph-deploy/main/head/centos/el6/i386/',
            upload_files=[('file', 'ceph-deploy-1.0.0-0.el6.i386.rpm', b_('hello tharrrr'))]
        )

        # get archs for ceph-deploy
        result = session.app.get(
            '/binaries/ceph-deploy/main/head/centos/el6/',
        )

        assert result.json['i386'] == ['ceph-deploy-1.0.0-0.el6.i386.rpm']

    def test_two_projects_different_archs_flavored(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        session.app.post(
            '/binaries/ceph/giant/head/centos/el6/x86_64/flavors/default/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )

        session.app.post(
            '/binaries/ceph-deploy/main/head/centos/el6/i386/flavors/default/',
            upload_files=[('file', 'ceph-deploy-1.0.0-0.el6.i386.rpm', b_('hello tharrrr'))]
        )

        # get archs for ceph-deploy
        result = session.app.get(
            '/binaries/ceph-deploy/main/head/centos/el6/',
        )

        assert result.json['i386'] == ['ceph-deploy-1.0.0-0.el6.i386.rpm']

    def test_same_project_different_archs_should_not_pollute_other_endpoints(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        session.app.post(
            '/binaries/ceph/giant/head/centos/el6/x86_64/flavors/default/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )

        session.app.post(
            '/binaries/ceph/giant/head/centos/el6/i386/flavors/default/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.i386.rpm', b_('hello tharrrr'))]
        )

        # get the binary for an i386 url but for a different arch on the same
        # project. This should never happen, and we should get a 404
        result = session.app.get(
            '/binaries/ceph/giant/head/centos/el6/i386/flavors/default/ceph-9.0.0-0.el6.x86_64.rpm/',
            expect_errors=True
        )

        assert result.status_int == 404


class TestBinaryController(object):

    @pytest.mark.parametrize(
            'url',
            ['/binaries/ceph/giant/head/ceph/el6/x86_64/',
             '/binaries/ceph/giant/head/ceph/el6/x86_64/flavors/default/']
    )
    def test_single_binary_file_creates_resource(self, session, tmpdir, url):
        pecan.conf.binary_root = str(tmpdir)
        result = session.app.post(
            url,
            params={'force': 1},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        assert result.status_int == 201

    @pytest.mark.parametrize(
            'url',
            ['/binaries/ceph/giant/head/ceph/el6/x86_64/',
             '/binaries/ceph/giant/head/ceph/el6/x86_64/flavors/default/']
    )
    def test_put_is_not_allowed(self, session, tmpdir, url):
        pecan.conf.binary_root = str(tmpdir)
        session.app.post(
            url,
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        result = session.app.put(
            url,
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))],
            expect_errors=True,
        )
        assert result.status_int == 405

    @pytest.mark.parametrize(
            'url_post, url_get',
            [('/binaries/ceph/giant/head/ceph/el7/x86_64/',
              '/binaries/ceph/giant/head/ceph/el6/x86_64/'),
             ('/binaries/ceph/giant/head/ceph/el7/x86_64/flavors/default/',
              '/binaries/ceph/giant/head/ceph/el6/x86_64/flavors/default/')]
    )
    def test_archs_is_not_found(self, session, tmpdir, url_post, url_get):
        pecan.conf.binary_root = str(tmpdir)
        # post to a different distro but same arch
        result = session.app.post(
            url_post,
            params={'force': 1},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        result = session.app.get(
            url_get,
            expect_errors=True
        )
        assert result.status_int == 404

    @pytest.mark.parametrize(
            'url_post, url_get',
            [('/binaries/ceph/giant/head/ceph/el6/x86_64/',
            '/binaries/ceph/giant/head/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/'),
            ('/binaries/ceph/giant/head/ceph/el6/x86_64/flavors/default/',
            '/binaries/ceph/giant/head/ceph/el6/x86_64/flavors/default/ceph-9.0.0-0.el6.x86_64.rpm/')]
    )
    def test_single_binary_file_can_be_downloaded(self, session, tmpdir, url_post, url_get):
        pecan.conf.binary_root = str(tmpdir)
        session.app.post(
            url_post,
            params={'force': 1},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        result = session.app.get(url_get)
        assert result.status_int == 200

    def test_single_binary_file_can_be_deleted(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        session.app.post(
            '/binaries/ceph/giant/head/ceph/el6/x86_64/',
            params={'force': 1},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        result = session.app.get('/binaries/ceph/giant/head/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/')
        assert result.status_int == 200
        result = session.app.delete('/binaries/ceph/giant/head/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/')
        assert result.status_int == 204
        result = session.app.get('/binaries/ceph/giant/head/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/', expect_errors=True)
        assert result.status_int == 404

    @pytest.mark.parametrize(
            'url',
            ['/binaries/ceph/giant/head/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            '/binaries/ceph/giant/head/ceph/el6/x86_64/flavors/default/ceph-9.0.0-0.el6.x86_64.rpm/']
    )
    def test_binary_file_deletes_object_with_no_path(self, session, url):
        p = Project("ceph")
        Binary(
            "ceph-9.0.0-0.el6.x86_64.rpm",
            p,
            distro="ceph",
            distro_version="el6",
            ref="giant",
            arch="x86_64",
            sha1="head",
        )
        result = session.app.delete(url, expect_errors=True)
        assert result.status_int == 204

    @pytest.mark.parametrize(
            'url',
            ['/binaries/ceph/giant/head/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            '/binaries/ceph/giant/head/ceph/el6/x86_64/flavors/default/ceph-9.0.0-0.el6.x86_64.rpm/']
    )
    def test_delete_missing_binary_file(self, session, tmpdir, url):
        pecan.conf.binary_root = str(tmpdir)
        result = session.app.get(url, expect_errors=True)
        assert result.status_int == 404

    def test_binary_file_deleted_removes_project(self, session, tmpdir):
        # if a project has no binaries related to it after binary deletion, it is deleted as well
        pecan.conf.binary_root = str(tmpdir)
        session.app.post(
            '/binaries/ceph/giant/head/ceph/el6/x86_64/',
            params={'force': 1},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        result = session.app.delete('/binaries/ceph/giant/head/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/')
        assert result.status_int == 204
        p = Project.get(1)
        assert not p

    def test_binary_file_deleted_project_exists(self, session, tmpdir):
        # if a project has binaries related to it after binary deletion, it will still exist
        pecan.conf.binary_root = str(tmpdir)
        session.app.post(
            '/binaries/ceph/giant/head/ceph/el6/x86_64/',
            params={'force': 1},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        session.app.post(
            '/binaries/ceph/giant/head/ceph/el7/x86_64/',
            params={'force': 1},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        result = session.app.delete('/binaries/ceph/giant/head/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/')
        assert result.status_int == 204
        p = Project.get(1)
        assert p.name == "ceph"

    @pytest.mark.parametrize(
            'url_post, url_delete',
            [('/binaries/ceph/giant/head/ceph/el6/x86_64/',
            '/binaries/ceph/giant/head/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/'),
            ('/binaries/ceph/giant/head/ceph/el6/x86_64/flavors/default/',
            '/binaries/ceph/giant/head/ceph/el6/x86_64/flavors/default/ceph-9.0.0-0.el6.x86_64.rpm/')]
    )
    def test_binary_file_deleted_removes_repo(self, session, tmpdir, url_post, url_delete):
        # if a repo has no binaries related to it after binary deletion, it is deleted as well
        pecan.conf.binary_root = str(tmpdir)
        session.app.post(
            url_post,
            params={'force': 1},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        repo = Repo.get(1)
        assert repo
        result = session.app.delete(url_delete)
        assert result.status_int == 204
        repo = Repo.get(1)
        assert not repo

    def test_binary_file_deleted_repo_exists(self, session, tmpdir):
        # if a repo has binaries related to it after binary deletion, it will still exist
        pecan.conf.binary_root = str(tmpdir)
        session.app.post(
            '/binaries/ceph/giant/head/ceph/el6/x86_64/',
            params={'force': 1},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        session.app.post(
            '/binaries/ceph/giant/head/ceph/el6/x86_64/',
            params={'force': 1},
            upload_files=[('file', 'ceph-9.1.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        repo = Repo.get(1)
        assert repo
        result = session.app.delete('/binaries/ceph/giant/head/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/')
        assert result.status_int == 204
        repo = Repo.get(1)
        assert repo.needs_update

    @pytest.mark.parametrize(
            'url',
            ['/binaries/ceph/giant/head/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            '/binaries/ceph/giant/head/ceph/el6/x86_64/flavors/default/ceph-9.0.0-0.el6.x86_64.rpm/']
    )
    def test_auth_fails(self, session, url):
        result = session.app.post(
            url,
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))],
            headers={'Authorization': util.make_credentials(correct=False)},
            expect_errors=True
        )
        assert result.status_int == 401

    def test_new_binary_upload_creates_model_with_path_forced(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)

        session.app.post(
            '/binaries/ceph/giant/head/ceph/el6/x86_64/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        session.app.put(
            '/binaries/ceph/giant/head/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        session.app.put(
            '/binaries/ceph/giant/head/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )

        binary = Binary.get(1)
        assert binary.path.endswith('ceph/giant/head/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm')

    @pytest.mark.parametrize(
            'url_post, url_post_2',
            [('/binaries/ceph/giant/head/ceph/el6/x86_64/',
              '/binaries/ceph/giant/head/ceph/el6/x86_64/'),
             ('/binaries/ceph/giant/head/ceph/el6/x86_64/flavors/default/',
              '/binaries/ceph/giant/head/ceph/el6/x86_64/flavors/default/')]
    )
    def test_new_binary_upload_fails_with_existing(self, session, tmpdir, url_post, url_post_2):
        pecan.conf.binary_root = str(tmpdir)

        # we do a bunch of requests that do talk to the database
        session.app.post(
            url_post,
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        result = session.app.post(
            url_post_2,
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))],
            expect_errors=True
        )

        assert result.status_int == 400

    @pytest.mark.parametrize(
            'url_post, url_post_2',
            [('/binaries/ceph/giant/head/ceph/el7/x86_64/',
              '/binaries/ceph/giant/head/ceph/el6/x86_64/'),
             ('/binaries/ceph/giant/head/ceph/el7/x86_64/flavors/default/',
              '/binaries/ceph/giant/head/ceph/el6/x86_64/flavors/default/')]
    )
    def test_posting_twice__different_distro_ver_not_requires_force_flag(self, session, tmpdir, url_post, url_post_2):
        pecan.conf.binary_root = str(tmpdir)
        result = session.app.post(
            url_post,
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        result = session.app.post(
            url_post_2,
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        assert result.status_int == 201

    def test_posting_twice_updates_the_binary(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        session.app.post(
            '/binaries/ceph/giant/head/ceph/el6/x86_64/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        session.app.put(
            '/binaries/ceph/giant/head/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('something changed'))]
        )

        destination = os.path.join(
            pecan.conf.binary_root,
            'ceph/giant/head/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm'
        )
        contents = open(destination).read()
        assert contents == 'something changed'

    @pytest.mark.parametrize(
            'url_post, url_get',
            [('/binaries/ceph/giant/head/ceph/el6/x86_64/',
              '/binaries/ceph/giant/head/ceph/el6/x86_64/'),
             ('/binaries/ceph/giant/head/ceph/el6/x86_64/flavors/default/',
              '/binaries/ceph/giant/head/ceph/el6/x86_64/flavors/default/')]
    )
    def test_binary_tells_what_project_it_belongs_to(self, session, tmpdir, url_post, url_get):
        pecan.conf.binary_root = str(tmpdir)
        result = session.app.post(
            url_post,
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        response = session.app.get(url_get).json
        result = response['ceph-9.0.0-0.el6.x86_64.rpm']['project']
        assert result == 'ceph'

    @pytest.mark.parametrize(
            'url_post, url_get',
            [('/binaries/ceph/giant/head/ceph/el6/x86_64/',
              '/binaries/ceph/giant/head/ceph/el6/x86_64/'),
             ('/binaries/ceph/giant/head/ceph/el6/x86_64/flavors/default/',
              '/binaries/ceph/giant/head/ceph/el6/x86_64/flavors/default/')]
    )
    def test_binary_gets_size_computed(self, session, tmpdir, url_post, url_get):
        pecan.conf.binary_root = str(tmpdir)
        result = session.app.post(
            url_post,
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        response = session.app.get(url_get).json
        result = response['ceph-9.0.0-0.el6.x86_64.rpm']['size']
        assert result == 13

    @pytest.mark.parametrize(
            'url_post, url_get',
            [('/binaries/ceph/giant/head/ceph/el6/x86_64/',
              '/binaries/ceph/giant/head/ceph/el6/x86_64/'),
             ('/binaries/ceph/giant/head/ceph/el6/x86_64/flavors/default/',
              '/binaries/ceph/giant/head/ceph/el6/x86_64/flavors/default/')]
    )
    def test_binary_gets_checksum_computed(self, session, tmpdir, url_post, url_get):
        pecan.conf.binary_root = str(tmpdir)
        result = session.app.post(
            url_post,
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        response = session.app.get(url_get).json
        result = response['ceph-9.0.0-0.el6.x86_64.rpm']['checksum']
        assert len(result) == 128
        assert result.startswith('318b')

    def test_binary_gets_checksum_computed_when_updated(self, session, tmpdir):
        pecan.conf.binary_root = str(tmpdir)
        result = session.app.post(
            '/binaries/ceph/giant/head/ceph/el6/x86_64/',
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        response = session.app.get('/binaries/ceph/giant/head/ceph/el6/x86_64/').json
        result = response['ceph-9.0.0-0.el6.x86_64.rpm']['checksum']
        assert result.startswith('318b')
        session.app.put(
            '/binaries/ceph/giant/head/ceph/el6/x86_64/ceph-9.0.0-0.el6.x86_64.rpm/',
            params={'force': True},
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('something changed'))]
        )
        response = session.app.get('/binaries/ceph/giant/head/ceph/el6/x86_64/').json
        result = response['ceph-9.0.0-0.el6.x86_64.rpm']['checksum']
        assert result.startswith('a5725e467')

    @pytest.mark.parametrize(
            'url_post, url_head',
            [('/binaries/ceph/giant/head/ceph/el6/x86_64/',
              '/binaries/ceph/giant/head/ceph/el6/x86_64/'),
             ('/binaries/ceph/giant/head/ceph/el6/x86_64/flavors/default/',
              '/binaries/ceph/giant/head/ceph/el6/x86_64/flavors/default/')]
    )
    def test_head_requests_are_allowed(self, session, tmpdir, url_post, url_head):
        pecan.conf.binary_root = str(tmpdir)
        session.app.post(
            url_post,
            upload_files=[('file', 'ceph-9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        response = session.app.head(url_head)
        assert response.status_int == 200


class TestRelatedProjects(object):

    @pytest.mark.parametrize(
            'url',
            ['/binaries/ceph-deploy/main/head/centos/6/x86_64/',
             '/binaries/ceph-deploy/main/head/centos/6/x86_64/flavors/default/']
    )
    def test_marks_nonexsitent_related_project(self, session, tmpdir, url):
        pecan.conf.binary_root = str(tmpdir)
        pecan.conf.repos = {
            'ceph': {
                'all': {'ceph-deploy': ['main']}
            },
            '__force_dict__': True,
        }
        session.app.post(
            url,
            upload_files=[('file', 'ceph-deploy_9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        project = Project.filter_by(name='ceph').first()
        # should've create the ceph project because it didn't exist
        assert project is not None
        repo = Repo.filter_by(project=project).first()
        assert repo.needs_update is True

    @pytest.mark.parametrize(
            'url',
            ['/binaries/ceph-deploy/main/head/centos/6/x86_64/',
             '/binaries/ceph-deploy/main/head/centos/6/x86_64/flavors/default/']
    )
    def test_marks_existing_related_project(self, session, tmpdir, url):
        pecan.conf.binary_root = str(tmpdir)
        pecan.conf.repos = {
            'ceph': {
                'all': {'ceph-deploy': ['main']}
            },
            '__force_dict__': True,
        }
        Project(name='ceph')
        session.commit()
        session.app.post(
            url,
            upload_files=[('file', 'ceph-deploy_9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        project = Project.filter_by(name='ceph').first()
        assert project is not None
        repo = Repo.filter_by(project=project).first()
        assert repo.needs_update is True

    @pytest.mark.parametrize(
            'url',
            ['/binaries/ceph-deploy/main/head/centos/6/x86_64/',
             '/binaries/ceph-deploy/main/head/centos/6/x86_64/flavors/default/']
    )
    def test_marks_multiple_projects(self, session, tmpdir, url):
        pecan.conf.binary_root = str(tmpdir)
        pecan.conf.repos = {
            'ceph': {
                'all': {'ceph-deploy': ['main']},
            },
            'rhcs': {
                'all': {'ceph-deploy': ['main']},
            },
            '__force_dict__': True,
        }
        session.commit()
        session.app.post(
            url,
            upload_files=[('file', 'ceph-deploy_9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        ceph_project = Project.filter_by(name='ceph').first()
        rhcs_project = Project.filter_by(name='rhcs').first()
        assert Repo.filter_by(project=ceph_project).first().needs_update is True
        assert Repo.filter_by(project=rhcs_project).first().needs_update is True

    @pytest.mark.parametrize(
            'url',
            ['/binaries/ceph-deploy/main/head/centos/6/x86_64/',
             '/binaries/ceph-deploy/main/head/centos/6/x86_64/flavors/default/']
    )
    def test_marks_nonexsitent_related_project_type(self, session, tmpdir, url):
        pecan.conf.binary_root = str(tmpdir)
        pecan.conf.repos = {
            'ceph': {
                'all': {'ceph-deploy': ['main']}
            },
            '__force_dict__': True,
        }
        session.app.post(
            url,
            upload_files=[('file', 'ceph-deploy_9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        project = Project.filter_by(name='ceph').first()
        repo = Repo.filter_by(project=project).first()
        assert repo.type == 'rpm'


class TestAutomaticRepos(object):
    # these are not unittests :(

    @pytest.mark.parametrize(
            'url',
            ['/binaries/ceph-deploy/main/head/centos/6/x86_64/',
             '/binaries/ceph-deploy/main/head/centos/6/x86_64/flavors/default/']
    )
    def test_skips_marking_needs_update_on_related_repos(self, session, tmpdir, url):
        pecan.conf.binary_root = str(tmpdir)
        pecan.conf.repos = {
            'ceph': {
                'automatic': False,
                'all': {'ceph-deploy': ['main']}
            },
            '__force_dict__': True,
        }
        session.app.post(
            url,
            upload_files=[('file', 'ceph-deploy_9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        project = Project.filter_by(name='ceph').first()
        repo = Repo.filter_by(project=project).first()
        # newly created repos will default to ``needs_update`` as ``True``,
        # revert so we can test if disabling automatic repos works
        repo.needs_update = False
        session.commit()

        session.app.post(
            url,
            upload_files=[('file', 'ceph-deploy_10.0.0-0.el6.x86_64.rpm', b_('newer version'))]
        )
        project = Project.filter_by(name='ceph').first()
        repo = Repo.filter_by(project=project).first()
        assert repo.needs_update is False

    @pytest.mark.parametrize(
            'url',
            ['/binaries/ceph-deploy/main/head/centos/6/x86_64/',
             '/binaries/ceph-deploy/main/head/centos/6/x86_64/flavors/default/']
    )
    def test_skips_marking_needs_update(self, session, tmpdir, url):
        pecan.conf.binary_root = str(tmpdir)
        pecan.conf.repos = {
            'ceph-deploy': {
                'automatic': False,
            },
            '__force_dict__': True,
        }
        session.app.post(
            url,
            upload_files=[('file', 'ceph-deploy_9.0.0-0.el6.x86_64.rpm', b_('hello tharrrr'))]
        )
        project = Project.filter_by(name='ceph-deploy').first()
        repo = Repo.filter_by(project=project).first()
        # newly created repos will default to ``needs_update`` as ``True``,
        # revert so we can test if disabling automatic repos works
        repo.needs_update = False
        session.commit()

        session.app.post(
            url,
            upload_files=[('file', 'ceph-deploy_10.0.0-0.el6.x86_64.rpm', b_('newer version'))]
        )
        project = Project.filter_by(name='ceph-deploy').first()
        repo = Repo.filter_by(project=project).first()
        assert repo.needs_update is False
