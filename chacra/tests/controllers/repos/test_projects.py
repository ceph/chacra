from chacra.models import Project, Repo


class TestProjectsController(object):

    def test_get_index_no_projects(self, session):
        result = session.app.get('/repos/')
        assert result.status_int == 200
        assert result.json == {}

    def test_project_no_built_repos(self, session):
        Project('foobar')
        session.commit()
        result = session.app.get('/repos/')
        assert result.status_int == 200
        assert result.json == {}

    def test_single_project_with_built_repos(self, session):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.get('/repos/')
        assert result.status_int == 200
        assert len(result.json) == 1
        assert result.json == {"foobar": ["firefly"]}

    def test_do_not_show_refs_without_built_repos(self, session):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        Repo(
            p,
            "hammer",
            "ubuntu",
            "trusty",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.get('/repos/')
        assert result.status_int == 200
        assert len(result.json) == 1
        assert result.json == {"foobar": ["firefly"]}

    def test_do_not_list_projects_without_built_repos(self, session):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        repo.path = "some_path"
        Project('baz')
        session.commit()
        result = session.app.get('/repos/')
        assert result.status_int == 200
        assert len(result.json) == 1
        assert result.json == {"foobar": ["firefly"]}


class TestProjectController(object):

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
        result = session.app.get('/repos/foobar/')
        assert result.status_int == 200
        assert len(result.json) == 1
        assert result.json == {"firefly": ["ubuntu"]}

    def test_project_does_not_exist(self, session):
        result = session.app.get('/repos/foo/', expect_errors=True)
        assert result.status_int == 404

    def test_project_has_no_built_repos(self, session):
        Project('foobar')
        result = session.app.get('/repos/foobar/', expect_errors=True)
        assert result.status_int == 404

    def test_do_not_show_refs_without_built_repos(self, session):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        Repo(
            p,
            "hammer",
            "ubuntu",
            "trusty",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.get('/repos/foobar/')
        assert result.status_int == 200
        assert len(result.json) == 1
        assert result.json == {"firefly": ["ubuntu"]}

    def test_show_multiple_refs_with_built_repos(self, session):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        repo2 = Repo(
            p,
            "hammer",
            "ubuntu",
            "trusty",
        )
        repo.path = "some_path"
        repo2.path = "some_path"
        session.commit()
        result = session.app.get('/repos/foobar/')
        assert result.status_int == 200
        assert len(result.json) == 2
        assert result.json == {"firefly": ["ubuntu"], "hammer": ["ubuntu"]}
