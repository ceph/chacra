import random
import string
import pytest
from chacra import util


source_rpms = [
    "%s-%s.src.rpm" % (
        ''.join(random.choice(string.ascii_letters) for _ in range(10)),
        '.'.join(random.choice(string.digits) for _ in range(3))
    ) for i in range(10)
] + [
    'ceph-deploy.SRC.rpm',
]

x64_rpms = [
    "%s-%s.x86_64.rpm" % (
        ''.join(random.choice(string.ascii_letters) for _ in range(10)),
        '.'.join(random.choice(string.digits) for _ in range(3))
    ) for i in range(10)
] + [
    'ceph-deploy.X86_64.rpm',
]

noarch = [
    "%s-%s.noarch.rpm" % (
        ''.join(random.choice(string.ascii_letters) for _ in range(10)),
        '.'.join(random.choice(string.digits) for _ in range(3))
    ) for i in range(10)
] + [
    'somenoarch.rpm',
    'ceph-deploy-NOARCHY-.rpm'
]

undetermined = [
    'garbage.deb',
    'test.tar.gz',
    'removeme.txt'
]


class TestRepoDirectory(object):

    @pytest.mark.parametrize('binary', source_rpms)
    def test_source_rpm(self, binary):
        result = util.repo_directory(binary)
        assert result == 'SRPMS'

    @pytest.mark.parametrize('binary', x64_rpms)
    def test_x64_rpm(self, binary):
        result = util.repo_directory(binary)
        assert result == 'x86_64'

    @pytest.mark.parametrize('binary', noarch)
    def test_noarch(self, binary):
        result = util.repo_directory(binary)
        assert result == 'noarch'

    @pytest.mark.parametrize('binary', undetermined)
    def test_undetermined(self, binary):
        result = util.repo_directory(binary)
        assert result == 'noarch'
