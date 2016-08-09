from chacra.models import Project, Repo


class TestSHA1Controller(object):

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
        result = session.app.get('/repos/foobar/firefly/head/')
        assert result.status_int == 200
        assert len(result.json) == 1
        assert result.json == {"ubuntu": ["trusty"]}

    def test_sha1_does_not_exist(self, session):
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
        result = session.app.get('/repos/foobar/firefly/sha1/', expect_errors=True)
        assert result.status_int == 404

    def test_sha1_has_no_built_repos(self, session):
        p = Project('foobar')
        Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        session.commit()
        result = session.app.get('/repos/foobar/firefly/head/')
        assert result.status_int == 200
        assert len(result.json) == 1

    def test_multiple_distros_with_built_repos(self, session):
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
            sha1="head",
        )
        repo.path = "some_path"
        repo2.path = "some_path"
        session.commit()
        result = session.app.get('/repos/foobar/firefly/head/')
        assert result.status_int == 200
        assert len(result.json) == 2
        assert result.json == {"ubuntu": ["trusty"], "centos": ['7']}
