"""Image and inspection metadata schemas for JalDrishti.

Maintained by Swastik Parmar (Backend / Integration Engineer).
Defines contracts for backend-controlled Cloudinary image ingestion,
responsive preview delivery, original inspection traceability,
and metadata persistence.
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ImageUploadResponse(BaseModel):
    """Public contract returned to frontend upon successful image upload."""

    model_config = ConfigDict(extra="ignore")

    image_id: str = Field(
        ..., description="Stable internal application-level image identifier"
    )
    inspection_id: Optional[str] = Field(
        default=None, description="Associated inspection or survey identifier"
    )
    status: str = Field(
        default="uploaded", description="Current status of the image asset"
    )
    preview_url: str = Field(
        ..., description="Optimized responsive preview URL for frontend presentation"
    )
    original_url: Optional[str] = Field(
        default=None,
        description="Secure delivery URL for the uncompressed original image",
    )
    format: str = Field(..., description="Verified image format (e.g. jpeg, png, webp)")
    width: int = Field(..., ge=1, description="Image width in pixels")
    height: int = Field(..., ge=1, description="Image height in pixels")
    bytes: int = Field(..., ge=0, description="Payload size in bytes")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")


class ImageMetadata(BaseModel):
    """Full internal persistence record stored in SQLite metadata repository."""

    model_config = ConfigDict(extra="ignore")

    image_id: str = Field(..., description="Stable internal unique identifier")
    inspection_id: Optional[str] = Field(
        default=None, description="Associated inspection session identifier"
    )
    public_id: str = Field(
        ..., description="Cloudinary storage public_id (backend-controlled)"
    )
    asset_id: Optional[str] = Field(
        default=None, description="Cloudinary unique asset identifier"
    )
    resource_type: str = Field(default="image", description="Resource type in storage")
    format: str = Field(..., description="Verified file format extension")
    width: int = Field(..., ge=1, description="Image width in pixels")
    height: int = Field(..., ge=1, description="Image height in pixels")
    bytes: int = Field(..., ge=0, description="Payload size in bytes")
    created_at: str = Field(..., description="ISO 8601 upload timestamp")
    status: str = Field(default="uploaded", description="Lifecycle status")
    structure_type: Optional[str] = Field(
        default=None, description="Heritage typology (e.g. baoli, kund, vav)"
    )
    original_filename: Optional[str] = Field(
        default=None, description="Original uploaded filename"
    )
    preview_url: str = Field(
        ..., description="Optimized responsive preview URL"
    )
    secure_url: str = Field(
        ..., description="Cloudinary delivery / secure access URL"
    )

    def to_upload_response(self) -> ImageUploadResponse:
        """Project persistent metadata to public client response."""
        return ImageUploadResponse(
            image_id=self.image_id,
            inspection_id=self.inspection_id,
            status=self.status,
            preview_url=self.preview_url,
            original_url=self.secure_url,
            format=self.format,
            width=self.width,
            height=self.height,
            bytes=self.bytes,
            created_at=self.created_at,
        )


class ImageDeleteResponse(BaseModel):
    """Response returned upon image deletion request."""

    model_config = ConfigDict(extra="ignore")

    image_id: str = Field(..., description="Identifier of the deleted image")
    status: str = Field(..., description="Status ('deleted' or 'partial_failure')")
    detail: str = Field(..., description="Human-readable operational summary")
    cloudinary_deleted: bool = Field(
        ..., description="Whether Cloudinary asset was deleted"
    )
    metadata_deleted: bool = Field(
        ..., description="Whether persistent database record was deleted"
    )


class InspectionImagesListResponse(BaseModel):
    """List of all images associated with an inspection session."""

    model_config = ConfigDict(extra="ignore")

    inspection_id: str = Field(..., description="Inspection identifier")
    total: int = Field(..., ge=0, description="Total count of associated images")
    images: List[ImageUploadResponse] = Field(
        default_factory=list, description="Array of image descriptors"
    )
