import json
import logging

from app.core.context import request_id_var
from app.core.logging import JsonFormatter


def _record(msg="hello", **extra):
    rec = logging.LogRecord("t", logging.INFO, __file__, 1, msg, (), None)
    for k, v in extra.items():
        setattr(rec, k, v)
    return rec


def test_json_formatter_basic_fields():
    out = json.loads(JsonFormatter().format(_record("hi")))
    assert out["message"] == "hi" and out["level"] == "INFO" and out["logger"] == "t"
    assert out["request_id"] is None and "ts" in out


def test_json_formatter_includes_extras_and_request_id():
    token = request_id_var.set("req-12345678")
    try:
        out = json.loads(JsonFormatter().format(_record(status=200, path="/x")))
    finally:
        request_id_var.reset(token)
    assert out["status"] == 200 and out["path"] == "/x" and out["request_id"] == "req-12345678"


def test_json_formatter_includes_exception():
    try:
        raise ValueError("bad")
    except ValueError:
        import sys
        rec = logging.LogRecord("t", logging.ERROR, __file__, 1, "x", (), sys.exc_info())
    assert "ValueError" in json.loads(JsonFormatter().format(rec))["exc"]


def test_access_log_emitted_with_request_id(client, caplog):
    with caplog.at_level(logging.INFO, logger="app.access"):
        client.get("/api/v1/health?token=should-not-be-logged")
    rec = next(r for r in caplog.records if r.name == "app.access")
    assert rec.status == 200 and rec.path == "/api/v1/health"
    assert "should-not-be-logged" not in json.dumps(rec.__dict__, default=str)
