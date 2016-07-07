from chacra.async import checks


class TestIsHealthy(object):

    def test_is_not_healthy(self):
        def bad_check():
            raise RuntimeError()

        checks.system_checks = (bad_check,)
        assert checks.is_healthy() is False

    def test_is_healthy(self):
        checks.system_checks = (lambda: True,)
        assert checks.is_healthy() is True
