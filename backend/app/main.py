import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.db.session import dispose_engine

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level, settings.log_format)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        logger.info("startup", extra={"env": settings.app_env, "version": settings.app_version,
                                      "database": settings.safe_database_url})
        yield
        dispose_engine()
        logger.info("shutdown")

    docs = settings.docs_are_enabled
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Universal Engineering Intelligence & Learning Ecosystem",
        lifespan=lifespan,
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
        openapi_url="/openapi.json" if docs else None,
    )

    # Added first => inner. CORS is added last => outermost, so preflights and
    # error responses also receive CORS headers.
    app.add_middleware(RequestContextMiddleware)
    origins = settings.cors_origin_list
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
            expose_headers=["X-Request-ID"],
            max_age=600,
        )

    register_exception_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
