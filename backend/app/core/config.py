"""Core application configuration for JalDrishti backend.

Maintained by Swastik Parmar (Backend / Integration Engineer).
Provides strongly typed environment configuration with safe defaults.
"""

import os
from typing import List, Optional
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

    # Cloudinary configuration (backend only - secret NEVER exposed)
    cloudinary_cloud_name: Optional[str] = Field(
        default_factory=lambda: os.getenv("CLOUDINARY_CLOUD_NAME")
    )
    cloudinary_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("CLOUDINARY_API_KEY")
    )
    cloudinary_api_secret: Optional[str] = Field(
        default_factory=lambda: os.getenv("CLOUDINARY_API_SECRET")
    )
    cloudinary_folder: str = Field(
        default_factory=lambda: os.getenv("CLOUDINARY_FOLDER", "jaldrishti/inspections")
    )
    cloudinary_secure_delivery: bool = Field(
        default_factory=lambda: os.getenv("CLOUDINARY_SECURE_DELIVERY", "true").lower()
        in ("true", "1", "yes")
    )

    # Image upload policy configuration
    max_upload_size_bytes: int = Field(
        default_factory=lambda: int(
            os.getenv("MAX_UPLOAD_SIZE_BYTES", str(10 * 1024 * 1024))
        )
    )
    allowed_image_formats: List[str] = Field(
        default_factory=lambda: [
            fmt.strip().lower()
            for fmt in os.getenv("ALLOWED_IMAGE_FORMATS", "jpeg,jpg,png,webp").split(",")
            if fmt.strip()
        ]
    )

    # Metadata persistence configuration (SQLite)
    sqlite_db_path: str = Field(
        default_factory=lambda: os.getenv("SQLITE_DB_PATH", "data/jaldrishti.db")
    )

    @property
    def is_cloudinary_configured(self) -> bool:
        """Check if all necessary Cloudinary credentials are provided."""
        return bool(
            self.cloudinary_cloud_name
            and self.cloudinary_api_key
            and self.cloudinary_api_secret
        )


settings = Settings()
