from chacra import metrics


class TestHostname(object):

    def test_gets_short_hostname(self, fake):
        socket = fake(gethostname=lambda: 'chacra.ceph.com')
        result = metrics.short_hostname(_socket=socket)
        assert result == 'chacra'


class TestAppendSuffix(object):

    def test_gets_suffix_appended(self):
        result = metrics.append_suffix('chacra', 'expensive_function')
        assert result == 'chacra.expensive_function'

    def test_gets_suffix_appended_with_dotted_paths(self):
        result = metrics.append_suffix('chacra.async', 'add_rpms')
        assert result == 'chacra.async.add_rpms'


class TestGetPrefix(object):

    def test_with_secret(self, fake):
        conf = fake(graphite_api_key='1234')
        result = metrics.get_prefix(conf=conf, host='local')
        assert result == '1234.local'

    def test_no_secret(self, fake):
        conf = fake()
        result = metrics.get_prefix(conf=conf, host='local')
        assert result == 'local'
