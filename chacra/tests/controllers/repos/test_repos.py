import os
import py.test
from chacra.models import Project, Repo


class TestRepoApiController(object):

    @py.test.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/']
    )
    def test_repo_exists(self, session, url):
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
        result = session.app.get(url)
        assert result.status_int == 200
        assert result.json["distro_version"] == "trusty"
        assert result.json["distro"] == "ubuntu"
        assert result.json["ref"] == "firefly"
        assert result.json["sha1"] == "head"

    @py.test.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/']
    )
    def test_repo_is_not_queued(self, session, url):
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
        result = session.app.get(url)
        assert result.status_int == 200
        assert result.json["is_queued"] is False

    @py.test.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/']
    )
    def test_repo_is_not_updating(self, session, url):
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
        result = session.app.get(url)
        assert result.status_int == 200
        assert result.json["is_updating"] is False

    @py.test.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/']
    )
    def test_repo_type(self, session, url):
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
        result = session.app.get(url)
        assert result.status_int == 200
        assert result.json["type"] is None

    @py.test.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/precise/',
             '/repos/foobar/firefly/head/ubuntu/precise/flavors/default/']
    )
    def test_distro_version_does_not_exist(self, session, url):
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
        result = session.app.get(url, expect_errors=True)
        assert result.status_int == 404

    @py.test.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/centos/trusty/',
             '/repos/foobar/firefly/head/centos/trusty/flavors/default/']
    )
    def test_distro_does_not_exist(self, session, url):
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
        result = session.app.get(url, expect_errors=True)
        assert result.status_int == 404

    @py.test.mark.parametrize(
            'url',
            ['/repos/foobar/hammer/head/ubuntu/trusty/',
             '/repos/foobar/hammer/head/ubuntu/trusty/flavors/default/']
    )
    def test_ref_does_not_exist(self, session, url):
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
        result = session.app.get('/repos/foobar/hammer/head/ubuntu/trusty/', expect_errors=True)
        assert result.status_int == 404

    @py.test.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/sha1/ubuntu/trusty/',
             '/repos/foobar/firefly/sha1/ubuntu/trusty/flavors/default/']
    )
    def test_sha1_does_not_exist(self, session, url):
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
        result = session.app.get(url, expect_errors=True)
        assert result.status_int == 404

    @py.test.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/']
    )
    def test_update_single_field(self, session, url):
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
        repo_id = repo.id
        data = {"distro_version": "precise"}
        result = session.app.post_json(
            url,
            params=data,
        )
        assert result.status_int == 200
        updated_repo = Repo.get(repo_id)
        assert updated_repo.distro_version == "precise"
        assert result.json['distro_version'] == "precise"

    @py.test.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/']
    )
    def test_update_multiple_fields(self, session, url):
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
        repo_id = repo.id
        data = {"distro_version": "7", "distro": "centos"}
        result = session.app.post_json(
            url,
            params=data,
        )
        assert result.status_int == 200
        updated_repo = Repo.get(repo_id)
        assert updated_repo.distro_version == "7"
        assert updated_repo.distro == "centos"
        assert result.json['distro_version'] == "7"
        assert result.json['distro'] == "centos"

    @py.test.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/']
    )
    def test_update_invalid_fields(self, session, url):
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
        repo_id = repo.id
        data = {"bogus": "7", "distro": "centos"}
        result = session.app.post_json(
            url,
            params=data,
            expect_errors=True,
        )
        assert result.status_int == 400
        updated_repo = Repo.get(repo_id)
        assert updated_repo.distro == "ubuntu"

    @py.test.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/']
    )
    def test_update_empty_json(self, session, url):
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
        result = session.app.post_json(
            url,
            params=dict(),
            expect_errors=True,
        )
        assert result.status_int == 400

    @py.test.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/']
    )
    def test_update_invalid_field_value(self, session, url):
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
        data = {"distro": 123}
        result = session.app.post_json(
            url,
            params=data,
            expect_errors=True,
        )
        assert result.status_int == 400


class TestRepoCRUDOperations(object):

    @py.test.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/update',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/update']
    )
    def test_update(self, session, tmpdir, url):
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
        repo.get(1)
        repo.needs_update = False
        session.commit()
        result = session.app.post_json(
            url,
            params={}
        )
        assert result.json['needs_update'] is True
        assert result.json['is_queued'] is False

    @py.test.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/update',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/update']
    )
    def test_update_head(self, session, tmpdir, url):
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
        result = session.app.head(url)
        assert result.status_int == 200

    @py.test.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/recreate',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/recreate']
    )
    def test_recreate(self, session, tmpdir, url):
        path = str(tmpdir)
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = path
        session.commit()
        result = session.app.post_json(url, params={})
        assert os.path.exists(path) is False
        assert result.json['needs_update'] is True
        assert result.json['is_queued'] is False

    @py.test.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/recreate',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/recreate']
    )
    def test_recreate_and_requeue(self, session, tmpdir, url):
        path = str(tmpdir)
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = path
        session.commit()
        repo = Repo.get(1)
        repo.is_queued = True
        session.commit()
        result = session.app.post_json(url)
        assert os.path.exists(path) is False
        assert result.json['needs_update'] is True
        assert result.json['is_queued'] is False

    @py.test.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/recreate',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/recreate']
    )
    def test_recreate_invalid_path(self, session, tmpdir, url):
        path = str(tmpdir)
        invalid_path = os.path.join(path, 'invalid_path')
        p = Project('foobar')
        repo = Repo(
            p,
            "firefly",
            "ubuntu",
            "trusty",
            sha1="head",
        )
        repo.path = invalid_path
        session.commit()
        result = session.app.post_json(url)
        assert os.path.exists(path) is True
        assert result.json['needs_update'] is True

    @py.test.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/recreate',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/recreate']
    )
    def test_recreate_head(self, session, tmpdir, url):
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
        result = session.app.head(url)
        assert result.status_int == 200

    @py.test.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/recreate',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/recreate']
    )
    def test_recreate_head_not_found(self, session, tmpdir, url):
        # probably overkill
        result = session.app.head(
            url,
            expect_errors=True,
        )
        assert result.status_int == 404

    @py.test.mark.parametrize(
            'url',
            ['/repos/foobar/firefly/head/ubuntu/trusty/recreate',
             '/repos/foobar/firefly/head/ubuntu/trusty/flavors/default/recreate']
    )
    def test_create_head_not_found(self, session, tmpdir, url):
        # probably overkill
        result = session.app.head(
            url,
            expect_errors=True,
        )
        assert result.status_int == 404
