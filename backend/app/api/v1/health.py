import logging

from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.schemas import HealthResponse, ReadinessResponse
from app.core.config import get_settings
from app.core.errors import AppError, ErrorResponse
from app.db.session import check_database, get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
def health() -> HealthResponse:
    """Process is up. Does not touch the database (safe for container healthchecks)."""
    return HealthResponse(status="ok", service="engiverse-api", version=get_settings().app_version)


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    responses={503: {"model": ErrorResponse}},
    summary="Readiness probe",
)
def readiness(db: Session = Depends(get_db)) -> ReadinessResponse:
    """Ready only if PostgreSQL answers a trivial query."""
    try:
        check_database(db)
    except SQLAlchemyError:
        logger.warning("readiness_database_unavailable", exc_info=True)
        raise AppError(503, "database_unavailable", "Database is not reachable.") from None
    return ReadinessResponse(
        status="ok", service="engiverse-api",
        version=get_settings().app_version, database="ok",
    )
