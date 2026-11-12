"""Import every ORM model module here so Base.metadata is complete for Alembic.

0.1.1 intentionally defines no tables (identity models arrive in 0.2).
"""
from app.db.base import Base  # noqa: F401
