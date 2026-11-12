"""Run against a real PostgreSQL:  TEST_DATABASE_URL=postgresql+psycopg://... pytest -m integration"""
import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.db.session import get_db

URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not URL, reason="TEST_DATABASE_URL not set"),
]


def test_real_select_1():
    engine = create_engine(URL, connect_args={"connect_timeout": 5})
    with engine.connect() as conn:
        assert conn.execute(text("SELECT 1")).scalar() == 1
    engine.dispose()


def test_readiness_against_real_database(app, client):
    engine = create_engine(URL, connect_args={"connect_timeout": 5})
    factory = sessionmaker(bind=engine)

    def _db():
        s = factory()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _db
    assert client.get("/api/v1/health/ready").status_code == 200
    engine.dispose()
