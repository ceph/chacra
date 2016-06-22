from chacra import metrics


class TestHostname(object):

    def test_gets_short_hostname(self, fake):
        socket = fake(gethostname=lambda: 'chacra.ceph.com')
        result = metrics.short_hostname(socket=socket)
        assert result == 'chacra'


class TestAppendSuffix(object):

    def test_gets_suffix_appended(self):
        result = metrics.append_suffix('chacra', 'expensive_function')
        assert result == 'chacra.expensive_function'

    def test_gets_suffix_appended_with_dotted_paths(self):
        result = metrics.append_suffix('chacra.async', 'add_rpms')
        assert result == 'chacra.async.add_rpms'
