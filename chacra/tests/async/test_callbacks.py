import os
import pytest
from pecan import conf
import requests
from chacra import async
from chacra.async import recurring
from chacra.models import Repo, Project
from chacra.tests import conftest


repo_keys = [
        '"needs_update"', '"sha1"', '"is_queued"', '"is_updating"', '"type"',
        '"modified"', '"signed"', '"status"', '"project_name"', '"distro_version"',
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

    def teardown(self):
        # callback settings added in test_post_request are "sticky", this
        # ensures they are reset for other tests that rely on pristine conf
        # settings
        conftest.reload_config()

    @pytest.mark.parametrize('key', repo_keys)
    def test_post_request(self, session, recorder, key):
        conf.callback_url = 'http://localhost/callback'
        f_async = recorder()
        async.post_status('building', self.repo, _callback=f_async)
        result = f_async.recorder_calls[0]['kwargs']['args'][0]
        assert key in result
        assert '"building"' in result


class TestCallbackInvalidConf(object):

    def setup(self):
        conf.callback_url = 'http://localhost/callback'

    def teardown(self):
        # callback settings added in setup are "sticky", this ensures they are
        # reset for other tests that rely on pristine conf settings
        conftest.reload_config()

    def test_missing_user_and_key(self):
        assert recurring.callback("{}", 'ceph') is False

    def test_missing_user(self):
        conf.callback_key = 'key'
        assert recurring.callback("{}", 'ceph') is False

    def test_missing_key(self):
        conf.callback_user = 'admin'
        assert recurring.callback("{}", 'ceph') is False


class TestCallback(object):

    def setup(self):
        conf.callback_url = 'http://localhost/callback'
        conf.callback_user = 'admin'
        conf.callback_key = 'key'

    def teardown(self):
        # callback settings added in setup are "sticky", this ensures they are
        # reset for other tests that rely on pristine conf settings
        conftest.reload_config()

    def test_invalid_json(self):
        # omg this is so invalid
        assert recurring.callback({'error': Exception}, 'ceph') is False

    def test_requests_correct_project_url(self, monkeypatch, recorder):
        r = recorder()
        monkeypatch.setattr(recurring.requests, 'post', r)
        recurring.callback("{}", 'ceph')
        result = r.recorder_calls[0]['args'][0]
        assert result == os.path.join(conf.callback_url, 'ceph', '')

    def test_requests_http_error(self, monkeypatch, fake):
        # not confident this is testing what really happens. Could not get the
        # 'retry' behavior from Celery. This just executes the code path to get
        # to the exception being re-raised by Celery, which might be enough
        def bad_post(*a, **kw):
            raise requests.HTTPError('I suck')
        monkeypatch.setattr(recurring.requests, 'post', bad_post)
        with pytest.raises(requests.HTTPError):
            recurring.callback("{}", 'ceph')
