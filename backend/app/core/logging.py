"""Structured logging (stdlib only). JSON lines in production, text in dev."""
import json
import logging
import sys
from datetime import datetime, timezone

from app.core.context import request_id_var

_STANDARD_ATTRS = frozenset(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(),
        }
        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=False)


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get() or "-"
        return True


def configure_logging(level: str = "INFO", fmt: str = "json") -> None:
    """Idempotently (re)configure the root logger."""
    handler = logging.StreamHandler(sys.stdout)
    if fmt == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.addFilter(_RequestIdFilter())
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)-8s [%(request_id)s] %(name)s: %(message)s")
        )
    handler._engiverse = True  # type: ignore[attr-defined]
    root = logging.getLogger()
    # Replace only our own previously-installed handler; leave foreign ones
    # (pytest capture, uvicorn, etc.) untouched.
    root.handlers[:] = [h for h in root.handlers if not getattr(h, "_engiverse", False)]
    root.addHandler(handler)
    root.setLevel(level)
    # The request middleware emits one structured access log per request.
    logging.getLogger("uvicorn.access").disabled = True
