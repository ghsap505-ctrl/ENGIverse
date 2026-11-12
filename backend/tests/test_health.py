from sqlalchemy.exc import OperationalError

from app.db.session import get_db


class _OkSession:
    def execute(self, *_a, **_k):
        return None


class _DownSession:
    def execute(self, *_a, **_k):
        raise OperationalError("SELECT 1", {}, Exception("connection refused: secret-host"))


def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["service"] == "engiverse-api"
    assert body["version"] == "0.1.2"


def test_api_root_preserved(client):
    r = client.get("/api/v1")
    assert r.status_code == 200
    assert r.json()["name"] == "ENGIverse API"


def test_readiness_ok(app, client):
    app.dependency_overrides[get_db] = lambda: _OkSession()
    r = client.get("/api/v1/health/ready")
    assert r.status_code == 200 and r.json()["database"] == "ok"


def test_readiness_503_does_not_leak_internal_error(app, client):
    app.dependency_overrides[get_db] = lambda: _DownSession()
    r = client.get("/api/v1/health/ready")
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "database_unavailable"
    assert "secret-host" not in r.text
