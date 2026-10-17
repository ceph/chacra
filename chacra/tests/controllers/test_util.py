import io
import os

import pytest

from chacra.controllers.util import write_file


class FailingFile(io.BytesIO):

    def read(self, *args):
        raise IOError('connection reset')


class TestWriteFile(object):

    def test_writes_the_file(self, tmpdir):
        destination = str(tmpdir.join('ceph.rpm'))
        write_file(io.BytesIO(b'new'), destination)
        with open(destination, 'rb') as f:
            assert f.read() == b'new'
        assert os.listdir(str(tmpdir)) == ['ceph.rpm']

    def test_failed_write_keeps_the_old_file(self, tmpdir):
        destination = tmpdir.join('ceph.rpm')
        destination.write('old')
        with pytest.raises(IOError):
            write_file(FailingFile(), str(destination))
        assert destination.read() == 'old'
        assert os.listdir(str(tmpdir)) == ['ceph.rpm']
