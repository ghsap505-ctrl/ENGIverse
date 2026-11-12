import pytest

from app.db import session as db_session
from conftest import make_settings


class _FakeSession:
    def __init__(self):
        self.rolled_back = self.closed = False

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


@pytest.fixture(autouse=True)
def _reset_engine():
    db_session.dispose_engine()
    yield
    db_session.dispose_engine()


def test_engine_is_lazy_and_pool_configured(monkeypatch):
    pytest.importorskip("psycopg")
    monkeypatch.setattr(db_session, "get_settings", lambda: make_settings(
        db_pool_size=3, db_max_overflow=2, db_pool_timeout=7))
    assert db_session._engine is None  # importing/constructing opened nothing
    engine = db_session.get_engine()   # creates engine; still no connection
    assert engine.pool.size() == 3 and engine.pool.timeout() == 7
    assert "unit-test-pass" not in str(engine.url)  # URL renders masked
    assert db_session.get_engine() is engine        # singleton


def test_get_db_closes_on_success(monkeypatch):
    fake = _FakeSession()
    monkeypatch.setattr(db_session, "get_session_factory", lambda: (lambda: fake))
    gen = db_session.get_db()
    assert next(gen) is fake
    gen.close()
    assert fake.closed and not fake.rolled_back


def test_get_db_rolls_back_and_closes_on_error(monkeypatch):
    fake = _FakeSession()
    monkeypatch.setattr(db_session, "get_session_factory", lambda: (lambda: fake))
    gen = db_session.get_db()
    next(gen)
    with pytest.raises(RuntimeError):
        gen.throw(RuntimeError("boom"))
    assert fake.rolled_back and fake.closed
