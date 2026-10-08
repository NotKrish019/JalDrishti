"""Health check response schema for JalDrishti backend."""

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Standardized health check status payload."""

    model_config = ConfigDict(extra="forbid")

    status: str = "ok"
    project: str = "jaldrishti"
    version: str = "0.1.0"
