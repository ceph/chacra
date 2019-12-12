import pytest
import subprocess
from chacra.async import rpm


class TestRPM(object):

    @pytest.mark.parametrize("distro", ['opensuse', 'openSUSE', 'sle', 'SLE'])
    def test__createrepo_opensuse(self, monkeypatch, distro):
        repo_dirs = ['basepath/noarch', 'basepath/x86_64']
        basepath = 'basepath'
        def mock_check_call(*args, **kwargs):
            assert args == (['createrepo', '--no-database', basepath],)

        monkeypatch.setattr(subprocess, 'check_call', mock_check_call)
        rpm._createrepo(basepath, repo_dirs, distro)

    @pytest.mark.parametrize("distro", ['centos', 'Fedora', 'RHEL'])
    def test__createrepo_other(self, monkeypatch, distro):
        repo_dirs = ['basepath/noarch', 'basepath/x86_64']
        basepath = 'basepath'
        def mock_check_call(*args, **kwargs):
            assert args == (['createrepo', '--no-database', repo_dirs.pop(0)],)

        monkeypatch.setattr(subprocess, 'check_call', mock_check_call)
        rpm._createrepo(basepath, repo_dirs, distro)
