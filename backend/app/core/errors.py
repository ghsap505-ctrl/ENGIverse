"""Uniform error envelope: {"error": {"code", "message", "request_id", "details"?}}.

Validation errors omit the submitted input so secrets (e.g. passwords in later
phases) are never reflected back or logged.
"""
import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

_STATUS_CODES = {
    400: "bad_request", 401: "unauthorized", 403: "forbidden", 404: "not_found",
    405: "method_not_allowed", 409: "conflict", 413: "payload_too_large",
    422: "validation_error", 429: "rate_limited", 503: "service_unavailable",
}


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str | None = None
    details: list[dict[str, Any]] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class AppError(Exception):
    """Raise from application code to produce a clean, typed error response."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code, self.code, self.message = status_code, code, message


def _response(request: Request, status: int, code: str, message: str,
              details: list[dict[str, Any]] | None = None,
              headers: dict[str, str] | None = None) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    body = ErrorResponse(error=ErrorBody(code=code, message=message,
                                         request_id=request_id, details=details))
    out = dict(headers or {})
    if request_id:
        out["X-Request-ID"] = request_id
    return JSONResponse(status_code=status, content=body.model_dump(exclude_none=True), headers=out)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError) -> JSONResponse:
        return _response(request, exc.status_code, exc.code, exc.message)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _STATUS_CODES.get(exc.status_code, "http_error")
        message = exc.detail if isinstance(exc.detail, str) else "Request failed."
        return _response(request, exc.status_code, code, message,
                         headers=dict(exc.headers or {}))

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {"loc": [str(part) for part in err.get("loc", ())],
             "message": err.get("msg", "Invalid value"),
             "type": err.get("type", "value_error")}
            for err in exc.errors()
        ]
        return _response(request, 422, "validation_error", "Request validation failed.", details)

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception", extra={"path": request.url.path})
        return _response(request, 500, "internal_error", "An internal error occurred.")
