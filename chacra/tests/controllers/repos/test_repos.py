import os
from chacra.models import Project, Repo


class TestRepoApiController(object):

    def test_repo_exists(self, session):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.get('/repos/foobar/firefly/ubuntu/trusty/')
        assert result.status_int == 200
        assert result.json["distro_version"] == "trusty"
        assert result.json["distro"] == "ubuntu"
        assert result.json["ref"] == "firefly"

    def test_distro_version_does_not_exist(self, session):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.get('/repos/foobar/firefly/ubuntu/precise/', expect_errors=True)
        assert result.status_int == 404

    def test_distro_does_not_exist(self, session):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.get('/repos/foobar/firefly/centos/trusty/', expect_errors=True)
        assert result.status_int == 404

    def test_ref_does_not_exist(self, session):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.get('/repos/foobar/hammer/ubuntu/trusty/', expect_errors=True)
        assert result.status_int == 404

    def test_update_single_field(self, session):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        repo.path = "some_path"
        session.commit()
        repo_id = repo.id
        data = {"distro_version": "precise"}
        result = session.app.post_json(
            "/repos/foobar/firefly/ubuntu/trusty/",
            params=data,
        )
        assert result.status_int == 200
        updated_repo = Repo.get(repo_id)
        assert updated_repo.distro_version == "precise"
        assert result.json['distro_version'] == "precise"

    def test_update_multiple_fields(self, session):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        repo.path = "some_path"
        session.commit()
        repo_id = repo.id
        data = {"distro_version": "7", "distro": "centos"}
        result = session.app.post_json(
            "/repos/foobar/firefly/ubuntu/trusty/",
            params=data,
        )
        assert result.status_int == 200
        updated_repo = Repo.get(repo_id)
        assert updated_repo.distro_version == "7"
        assert updated_repo.distro == "centos"
        assert result.json['distro_version'] == "7"
        assert result.json['distro'] == "centos"

    def test_update_invalid_fields(self, session):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        repo.path = "some_path"
        session.commit()
        repo_id = repo.id
        data = {"bogus": "7", "distro": "centos"}
        result = session.app.post_json(
            "/repos/foobar/firefly/ubuntu/trusty/",
            params=data,
            expect_errors=True,
        )
        assert result.status_int == 400
        updated_repo = Repo.get(repo_id)
        assert updated_repo.distro == "ubuntu"

    def test_update_empty_json(self, session):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.post_json(
            "/repos/foobar/firefly/ubuntu/trusty/",
            params=dict(),
            expect_errors=True,
        )
        assert result.status_int == 400

    def test_update_invalid_field_value(self, session):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        repo.path = "some_path"
        session.commit()
        data = {"distro": 123}
        result = session.app.post_json(
            "/repos/foobar/firefly/ubuntu/trusty/",
            params=data,
            expect_errors=True,
        )
        assert result.status_int == 400


class TestRepoCRUDOperations(object):

    def test_update(self, session, tmpdir):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        repo.path = "some_path"
        session.commit()
        repo.get(1)
        repo.needs_update = False
        session.commit()
        result = session.app.post_json(
            "/repos/foobar/firefly/ubuntu/trusty/update",
            params={}
        )
        assert result.json['needs_update'] is True

    def test_update_head(self, session, tmpdir):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.head(
            "/repos/foobar/firefly/ubuntu/trusty/update"
        )
        assert result.status_int == 200

    def test_recreate(self, session, tmpdir):
        path = str(tmpdir)
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        repo.path = path
        session.commit()
        result = session.app.post_json(
            "/repos/foobar/firefly/ubuntu/trusty/recreate",
            params={}
        )
        assert os.path.exists(path) is False
        assert result.json['needs_update'] is True

    def test_recreate_invalid_path(self, session, tmpdir):
        path = str(tmpdir)
        invalid_path = os.path.join(path, 'invalid_path')
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        repo.path = invalid_path
        session.commit()
        result = session.app.post_json(
            "/repos/foobar/firefly/ubuntu/trusty/recreate",
            params={}
        )
        assert os.path.exists(path) is True
        assert result.json['needs_update'] is True

    def test_recreate_head(self, session, tmpdir):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.head(
            "/repos/foobar/firefly/ubuntu/trusty/recreate"
        )
        assert result.status_int == 200

    def test_recreate_head_not_found(self, session, tmpdir):
        # probably overkill
        result = session.app.head(
            "/repos/foobar/firefly/ubuntu/trusty/recreate",
            expect_errors=True,
        )
        assert result.status_int == 404

    def test_create_head_not_found(self, session, tmpdir):
        # probably overkill
        result = session.app.head(
            "/repos/foobar/firefly/ubuntu/trusty/create",
            expect_errors=True,
        )
        assert result.status_int == 404
