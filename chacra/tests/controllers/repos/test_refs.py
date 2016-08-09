from chacra.models import Project, Repo


class TestRefController(object):

    def test_get_single_project(self, session):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.get('/repos/foobar/firefly/')
        assert result.status_int == 200
        assert len(result.json) == 1
        assert result.json == {"head": ["ubuntu"]}

    def test_ref_does_not_exist(self, session):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.get('/repos/foobar/hammer/', expect_errors=True)
        assert result.status_int == 404

    def test_ref_has_no_built_repos(self, session):
        p = Project('foobar')
        Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        session.commit()
        result = session.app.get('/repos/foobar/firefly/')
        assert result.status_int == 200
        assert len(result.json) == 1

    def test_does_show_sha1_without_built_repos(self, session):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="sha1",
        )
        Repo(
            p,
            "firefly",
            "centos",
            "7",
            sha1="head",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.get('/repos/foobar/firefly/')
        assert len(result.json) == 2
        assert "sha1" in result.json

    def test_multiple_sha1_with_built_repos(self, session):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo2 = Repo(
            p,
            "firefly",
            "centos",
            "7",
            sha1="sha1",
        )
        repo.path = "some_path"
        repo2.path = "some_path"
        session.commit()
        result = session.app.get('/repos/foobar/firefly/')
        assert result.status_int == 200
        assert len(result.json) == 2
        assert result.json == {"head": ["ubuntu"], "sha1": ['centos']}
