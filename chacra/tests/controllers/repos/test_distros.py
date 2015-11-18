from chacra.models import Project, Repo


class TestDistroController(object):

    def test_single_distro(self, session):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.get('/repos/foobar/firefly/ubuntu/')
        assert result.status_int == 200
        assert len(result.json) == 1
        assert result.json == ["trusty"]

    def test_does_not_show_duplicate_distro_versions(self, session):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        repo.path = "some_path"
        repo2 = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        repo2.path = "some_path"
        session.commit()
        result = session.app.get('/repos/foobar/firefly/ubuntu/')
        assert result.status_int == 200
        assert len(result.json) == 1
        assert result.json == ["trusty"]

    def test_shows_only_versions_for_ref(self, session):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        repo.path = "some_path"
        repo2 = Repo(
            p,
            "hammer",
            "ubuntu",
            "precise",
        )
        repo2.path = "some_path"
        session.commit()
        result = session.app.get('/repos/foobar/firefly/ubuntu/')
        assert result.status_int == 200
        assert len(result.json) == 1
        assert result.json == ["trusty"]

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
        result = session.app.get('/repos/foobar/firefly/centos/',
                                 expect_errors=True)
        assert result.status_int == 404

    def test_distro_has_no_built_repos(self, session):
        p = Project('foobar')
        Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
        )
        session.commit()
        result = session.app.get('/repos/foobar/firefly/ubuntu/',
                                 expect_errors=True)
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
        result = session.app.get('/repos/foobar/hammer/ubuntu/',
                                 expect_errors=True)
        assert result.status_int == 404
