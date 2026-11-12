from pydantic import BaseModel


class RootResponse(BaseModel):
    name: str
    version: str
    docs: str | None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ReadinessResponse(HealthResponse):
    database: str
