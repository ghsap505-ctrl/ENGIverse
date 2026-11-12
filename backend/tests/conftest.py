import os

# Must be set BEFORE importing app.main (which builds the app from env at import).
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://engiverse_test:unit-test-pass@localhost:5432/engiverse_test",
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402

GOOD_URL = "postgresql+psycopg://u:unit-test-pass@localhost:5432/db"
PROD_PASSWORD = "Zx9kQ2mV7pLr4Tn8Wd3Y"  # not a placeholder, >= 16 chars


def make_settings(**overrides) -> Settings:
    values = {"database_url": GOOD_URL, "app_env": "test", "log_format": "text"}
    values.update(overrides)
    return Settings(_env_file=None, **values)


@pytest.fixture
def settings_factory():
    return make_settings


@pytest.fixture
def app():
    return create_app(make_settings())


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
