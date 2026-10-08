"""Core application configuration for JalDrishti backend.

Maintained by Swastik Parmar (Backend / Integration Engineer).
Provides strongly typed environment configuration with safe defaults.
"""

import os
from typing import List
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings loaded from environment or defaults."""

    project_name: str = "JalDrishti API"
    project_slug: str = "jaldrishti"
    version: str = "0.1.0"
    description: str = "Jal-Dharohar Digital Intelligence & Conservation Platform API"

    # Server configuration
    host: str = Field(default_factory=lambda: os.getenv("BACKEND_HOST", "127.0.0.1"))
    port: int = Field(default_factory=lambda: int(os.getenv("BACKEND_PORT", "8000")))
    environment: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "info"))

    # CORS configuration - strict development origin for Vite PWA frontend
    cors_origins: List[str] = Field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
            if origin.strip()
        ]
    )


settings = Settings()
