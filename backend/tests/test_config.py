import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_app
from conftest import PROD_PASSWORD, make_settings


def test_database_url_is_required(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_password_required_and_not_leaked_in_error():
    with pytest.raises(ValidationError) as exc:
        make_settings(database_url="postgresql+psycopg://u@h:5432/d")
    assert "password" in str(exc.value).lower()
    with pytest.raises(ValidationError) as exc2:
        make_settings(database_url="postgresql://u:leakme-secret@h:5432/d")
    assert "leakme-secret" not in str(exc2.value)


def test_secret_not_in_repr_or_safe_url():
    s = make_settings()
    assert "unit-test-pass" not in repr(s)
    assert "unit-test-pass" not in s.safe_database_url


def test_production_placeholder_password_rejected():
    with pytest.raises(ValidationError):
        make_settings(app_env="production",
                      database_url="postgresql+psycopg://u:change-this-password@h:5432/d")


def test_production_valid_settings():
    s = make_settings(app_env="production",
                      database_url=f"postgresql+psycopg://u:{PROD_PASSWORD}@h:5432/d")
    assert s.is_production and s.docs_are_enabled is False


def test_wildcard_cors_rejected():
    with pytest.raises(ValidationError):
        make_settings(cors_origins="*")


def test_pool_bounds_validated():
    with pytest.raises(ValidationError):
        make_settings(db_pool_size=0)


def test_docs_disabled_in_production():
    s = make_settings(app_env="production",
                      database_url=f"postgresql+psycopg://u:{PROD_PASSWORD}@h:5432/d")
    with TestClient(create_app(s)) as c:
        assert c.get("/docs").status_code == 404
        assert c.get("/openapi.json").status_code == 404
        assert c.get("/api/v1/health").status_code == 200


def test_docs_enabled_in_development(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200
