from fastapi.testclient import TestClient

from app.main import create_app
from conftest import make_settings

ORIGIN = "http://localhost:5173"


def _preflight(c, origin):
    return c.options("/api/v1/health", headers={
        "Origin": origin, "Access-Control-Request-Method": "GET"})


def test_allowed_origin_gets_cors_headers():
    app = create_app(make_settings(cors_origins=f"{ORIGIN},http://127.0.0.1:5173"))
    with TestClient(app) as c:
        r = _preflight(c, ORIGIN)
        assert r.status_code == 200
        assert r.headers["access-control-allow-origin"] == ORIGIN
        assert r.headers["access-control-allow-credentials"] == "true"


def test_unlisted_origin_is_rejected():
    app = create_app(make_settings(cors_origins=ORIGIN))
    with TestClient(app) as c:
        r = _preflight(c, "http://evil.example")
        assert "access-control-allow-origin" not in r.headers


def test_no_origins_configured_means_no_cors():
    app = create_app(make_settings(cors_origins=""))
    with TestClient(app) as c:
        r = c.get("/api/v1/health", headers={"Origin": ORIGIN})
        assert "access-control-allow-origin" not in r.headers
