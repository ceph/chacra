from chacra.controllers import health


class TestHealthController(object):

    def test_passes_health_check(self, session, monkeypatch):
        monkeypatch.setattr(health.checks, "is_healthy", lambda: True)
        result = session.app.get("/health/")
        assert result.status_int == 200

    def test_fails_health_check(self, session, monkeypatch):
        monkeypatch.setattr(health.checks, "is_healthy", lambda: False)
        result = session.app.get("/health/", expect_errors=True)
        assert result.status_int == 500
