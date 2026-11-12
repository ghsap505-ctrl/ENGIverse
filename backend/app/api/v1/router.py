from fastapi import APIRouter

from app.api.v1 import health
from app.api.v1.schemas import RootResponse
from app.core.config import get_settings

api_router = APIRouter(prefix="/api/v1")


@api_router.get("", response_model=RootResponse, tags=["System"], include_in_schema=True)
def api_root() -> RootResponse:
    s = get_settings()
    return RootResponse(name="ENGIverse API", version=s.app_version,
                        docs="/docs" if s.docs_are_enabled else None)


api_router.include_router(health.router)
