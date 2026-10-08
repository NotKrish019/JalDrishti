"""Health check response schema for BaoliGuard backend."""

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Standardized health check status payload."""

    model_config = ConfigDict(extra="forbid")

    status: str = "ok"
    project: str = "baoliguard"
    version: str = "0.1.0"
