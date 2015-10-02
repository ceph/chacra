from chacra.models import Project, Repo


class TestRefController(object):

    def test_get_single_project(self, session):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.get('/repos/foobar/firefly/')
        assert result.status_int == 200
        assert len(result.json) == 1
        assert result.json == {"ubuntu": ["trusty"]}

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
        result = session.app.get('/repos/foobar/hammer/', expect_errors=True)
        assert result.status_int == 404

    def test_ref_has_no_built_repos(self, session):
        p = Project('foobar')
        Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        session.commit()
        result = session.app.get('/repos/foobar/firefly/', expect_errors=True)
        assert result.status_int == 404

    def test_do_not_show_distro_without_built_repos(self, session):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        Repo(
            p,
            "firefly",
            "centos",
            "7",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.get('/repos/foobar/firefly/')
        assert result.status_int == 200
        assert len(result.json) == 1
        assert result.json == {"ubuntu": ["trusty"]}

    def test_multiple_distros_with_built_repos(self, session):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        repo2 = Repo(
            p,
            "firefly",
            "centos",
            "7",
        )
        repo.path = "some_path"
        repo2.path = "some_path"
        session.commit()
        result = session.app.get('/repos/foobar/firefly/')
        assert result.status_int == 200
        assert len(result.json) == 2
        assert result.json == {"ubuntu": ["trusty"], "centos": ['7']}
