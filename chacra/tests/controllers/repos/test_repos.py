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
