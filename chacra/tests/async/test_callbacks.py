import pytest
from pecan import conf
from chacra import async
from chacra.models import Repo, Project


repo_keys = [
        '"needs_update"', '"sha1"', '"is_queued"', '"is_updating"', '"type"',
        '"modified"', '"signed"', '"state"', '"project_name"', '"distro_version"',
        '"path"', '"flavor"', '"ref"', '"distro"']


class TestHelpers(object):

    def setup(self):
        self.p = Project('ceph')
        self.repo = Repo(
            self.p,
            ref='firefly',
            distro='centos',
            distro_version='7',
            )

    @pytest.mark.parametrize('key', repo_keys)
    def test_post_request(self, monkeypatch, recorder, key):
        conf.callback_url = 'http://localhost/callback'
        f_async = recorder()
        async.post_status('building', self.repo, _callback=f_async)
        result = f_async.recorder_calls[0]['kwargs']['args'][0]
        assert key in result
