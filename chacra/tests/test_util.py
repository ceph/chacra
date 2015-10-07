import random
import string
import pytest
import pecan
from chacra import util
from chacra import models


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
        result = util.infer_arch_directory(binary)
        assert result == 'SRPMS'

    @pytest.mark.parametrize('binary', x64_rpms)
    def test_x64_rpm(self, binary):
        result = util.infer_arch_directory(binary)
        assert result == 'x86_64'

    @pytest.mark.parametrize('binary', noarch)
    def test_noarch(self, binary):
        result = util.infer_arch_directory(binary)
        assert result == 'noarch'

    @pytest.mark.parametrize('binary', undetermined)
    def test_undetermined(self, binary):
        result = util.infer_arch_directory(binary)
        assert result == 'noarch'


class TestRepoPaths(object):

    def setup(self):
        self.repo = models.Repo(
            models.Project('ceph-deploy'),
            'master',
            'centos',
            'el7'
        )

    def test_relative(self):
        pecan.conf.repos_root = '/tmp/repos'
        result = util.repo_paths(self.repo)
        assert result['relative'] == 'master/centos/el7'

    def test_root(self):
        pecan.conf.repos_root = '/tmp/repos'
        result = util.repo_paths(self.repo)
        assert result['root'] == '/tmp/repos/ceph-deploy'

    def test_absolute(self):
        pecan.conf.repos_root = '/tmp/repos'
        result = util.repo_paths(self.repo)['absolute']
        assert result == '/tmp/repos/ceph-deploy/master/centos/el7'
