import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.main import create_app
from conftest import make_settings


class Payload(BaseModel):
    password: str = Field(min_length=12)


@pytest.fixture
def err_app():
    app = create_app(make_settings())

    @app.post("/_t/validate")
    def validate(p: Payload):
        return {"ok": True}

    @app.get("/_t/boom")
    def boom():
        raise RuntimeError("internal detail that must not leak")

    return app


def test_404_uses_envelope(client):
    r = client.get("/nope")
    assert r.status_code == 404
    err = r.json()["error"]
    assert err["code"] == "not_found" and err["request_id"] == r.headers["X-Request-ID"]


def test_405_uses_envelope(client):
    r = client.post("/api/v1/health")
    assert r.status_code == 405 and r.json()["error"]["code"] == "method_not_allowed"


def test_validation_error_does_not_echo_input(err_app):
    with TestClient(err_app) as c:
        r = c.post("/_t/validate", json={"password": "short"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"
    assert "short-secret" not in r.text
    assert r.json()["error"]["details"][0]["loc"] == ["body", "password"]


def test_unhandled_exception_returns_generic_500(err_app):
    with TestClient(err_app, raise_server_exceptions=False) as c:
        r = c.get("/_t/boom")
    assert r.status_code == 500
    assert r.json()["error"]["code"] == "internal_error"
    assert "internal detail" not in r.text
    assert r.headers.get("X-Request-ID")


def test_valid_request_id_is_propagated(client):
    r = client.get("/api/v1/health", headers={"X-Request-ID": "abc12345-req"})
    assert r.headers["X-Request-ID"] == "abc12345-req"


def test_malicious_request_id_is_replaced(client):
    r = client.get("/api/v1/health", headers={"X-Request-ID": "x y\tinjected"})
    assert r.headers["X-Request-ID"] != "x y\tinjected" and len(r.headers["X-Request-ID"]) == 32


def test_security_headers_present(client):
    h = client.get("/api/v1/health").headers
    assert h["X-Content-Type-Options"] == "nosniff"
    assert h["X-Frame-Options"] == "DENY"
    assert h["Referrer-Policy"] == "no-referrer"
