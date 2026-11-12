"""Per-request context shared by middleware and logging (stdlib only)."""
from contextvars import ContextVar

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
