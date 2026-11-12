"""PostgreSQL connection management.

- The engine is created lazily: importing this module never opens a connection.
- Pool size/overflow/timeout/recycle come from Settings.
- pool_pre_ping discards dead connections (DB restarts, idle timeouts).
- One engine per process; with N uvicorn workers the DB sees up to
  N * (pool_size + max_overflow) connections. Size accordingly.
"""
from collections.abc import Iterator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        s = get_settings()
        _engine = create_engine(
            s.database_url.get_secret_value(),
            pool_size=s.db_pool_size,
            max_overflow=s.db_max_overflow,
            pool_timeout=s.db_pool_timeout,
            pool_recycle=s.db_pool_recycle,
            pool_pre_ping=True,
            echo=s.db_echo,
            connect_args={"connect_timeout": s.db_connect_timeout},
        )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(), autoflush=False, expire_on_commit=False
        )
    return _session_factory


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one session per request, always rolled back on error.

    Callers commit explicitly; uncommitted work is rolled back on close.
    """
    session = get_session_factory()()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_database(session: Session) -> None:
    """Raise SQLAlchemyError if the database cannot answer a trivial query."""
    session.execute(text("SELECT 1"))


def dispose_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
