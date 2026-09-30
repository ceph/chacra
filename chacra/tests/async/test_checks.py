import errno

import pytest
from chacra.asynch import checks
from chacra.asynch.checks import SystemCheckError


class TestIsHealthy(object):

    def test_is_not_healthy(self):
        def bad_check():
            raise RuntimeError()

        checks.system_checks = (bad_check,)
        assert checks.is_healthy() is False

    def test_is_healthy(self):
        checks.system_checks = (lambda: True,)
        assert checks.is_healthy() is True


class TestRabbitmqIsRunning(object):

    def fail_times(self, monkeypatch, times, error):
        calls = []

        def celery_has_workers():
            calls.append(1)
            if len(calls) <= times:
                raise error

        monkeypatch.setattr(checks, 'celery_has_workers', celery_has_workers)
        return calls

    def test_stale_connection_is_retried(self, monkeypatch):
        error = ConnectionResetError(errno.ECONNRESET, 'Connection reset by peer')
        calls = self.fail_times(monkeypatch, 1, error)
        assert checks.rabbitmq_is_running() is None
        assert len(calls) == 2

    def test_persistent_error_fails(self, monkeypatch):
        error = ConnectionResetError(errno.ECONNRESET, 'Connection reset by peer')
        calls = self.fail_times(monkeypatch, 2, error)
        with pytest.raises(SystemCheckError) as err:
            checks.rabbitmq_is_running()
        assert 'Error connecting to RabbitMQ' in err.value.message
        assert len(calls) == 2

    def test_connection_refused(self, monkeypatch):
        error = ConnectionRefusedError(errno.ECONNREFUSED, 'Connection refused')
        self.fail_times(monkeypatch, 2, error)
        with pytest.raises(SystemCheckError) as err:
            checks.rabbitmq_is_running()
        assert err.value.message == 'RabbitMQ is not running or not reachable'

    def test_no_workers_is_not_retried(self, monkeypatch):
        calls = self.fail_times(
            monkeypatch, 2, SystemCheckError('No running Celery worker was found'))
        with pytest.raises(SystemCheckError):
            checks.rabbitmq_is_running()
        assert len(calls) == 1


df_communicate = (
b'Filesystem                   1K-blocks    Used Available Use% Mounted on\n/dev/mapper/vagrant--vg-root  80909064 2205960  74570036   3% /\n',
'')

df_communicate_full = (
b'Filesystem                   1K-blocks    Used Available Use% Mounted on\n/dev/mapper/vagrant--vg-root  80909064 2205960  74570036   93% /\n',
'')

def fake_wait(timeout=0):
    return True

class TestDiskHasSpace(object):


    def test_it_has_plenty(self, fake):
        popen = fake(returncode=0, wait=fake_wait, communicate=lambda: df_communicate)
        result = checks.disk_has_space(_popen=lambda *a, **kw: popen)
        assert result is None

    def test_it_has_an_error(self, fake):
        stderr = fake(read=lambda: b'df had an error')
        popen = fake(returncode=1, wait=fake_wait, stderr=stderr)
        with pytest.raises(SystemCheckError) as err:
            checks.disk_has_space(_popen=lambda *a, **kw: popen)
        assert 'df had an error' in err.value.message

    def test_it_is_full(self, fake):
        popen = fake(returncode=0, wait=fake_wait, communicate=lambda: df_communicate_full)
        with pytest.raises(SystemCheckError) as err:
            checks.disk_has_space(_popen=lambda *a, **kw: popen)
        assert 'almost full. Used: 93%' in err.value.message


class TestErrorMessage(object):

    def test_message_is_captured(self):
        with pytest.raises(SystemCheckError) as err:
            raise SystemCheckError('an error message')
        assert 'an error message' == str(err.value)
