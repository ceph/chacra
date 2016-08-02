from chacra.models import Project, Repo


class TestFlavorsController(object):

    def test_default_flavor(self, session):
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
        result = session.app.get('/repos/foobar/firefly/head/ubuntu/trusty/flavors/')
        assert result.json == ['default']

    def test_multiple_flavors(self, session):
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = "some_path"
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
            flavor="tcmalloc",
        )
        repo.path = "some_path"
        session.commit()
        result = session.app.get('/repos/foobar/firefly/head/ubuntu/trusty/flavors/')
        assert sorted(result.json) == sorted(['default', 'tcmalloc'])
