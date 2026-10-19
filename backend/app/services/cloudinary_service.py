"""Backend Cloudinary Service for JalDrishti Heritage Platform.

Maintained by Swastik Parmar (Backend / Integration Engineer).
Encapsulates all interaction with Cloudinary:
- Backend-only configuration (API secret never exposed to frontend).
- Safe error handling without credential or payload leakage.
- Clear separation between responsive preview generation, full-resolution original delivery,
  and unmodified raw input for vision inference pipelines.
- Supports deletion with granular status reporting.
"""

import io
import logging
from typing import Any, Dict, List, Optional, Tuple

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class CloudinaryConfigError(Exception):
    """Raised when Cloudinary service is required but credentials are unconfigured."""
    pass


class CloudinaryUploadError(Exception):
    """Raised when Cloudinary upload operation encounters a provider error."""
    pass


class CloudinaryDeleteError(Exception):
    """Raised when Cloudinary asset deletion encounters a provider error."""
    pass


class CloudinaryService:
    """Service handling backend-controlled Cloudinary storage and URL derivation."""

    def __init__(self) -> None:
        self._is_initialized = False

    def is_configured(self) -> bool:
        """Verify whether required Cloudinary credentials are set in environment."""
        return settings.is_cloudinary_configured

    def _configure_sdk(self) -> None:
        """Configure Cloudinary SDK safely with environment settings."""
        if not self.is_configured():
            raise CloudinaryConfigError(
                "Cloudinary image storage service is not configured. "
                "Required backend environment variables: "
                "CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET."
            )

        try:
            import cloudinary
            import cloudinary.uploader

            cloudinary.config(
                cloud_name=settings.cloudinary_cloud_name,
                api_key=settings.cloudinary_api_key,
                api_secret=settings.cloudinary_api_secret,
                secure=settings.cloudinary_secure_delivery,
            )
            self._is_initialized = True
        except Exception as e:
            logger.error("Failed to configure Cloudinary SDK: %s", type(e).__name__)
            raise CloudinaryConfigError(f"Cloudinary initialization failed: {type(e).__name__}") from e

    def build_preview_url(self, public_id: str, format_ext: Optional[str] = None) -> str:
        """Derive responsive web preview URL with auto-optimization transformations."""
        try:
            import cloudinary.utils

            url, _ = cloudinary.utils.cloudinary_url(
                public_id,
                format=format_ext,
                secure=settings.cloudinary_secure_delivery,
                transformation=[
                    {"width": 800, "crop": "limit"},
                    {"quality": "auto"},
                    {"fetch_format": "auto"},
                ],
            )
            return url
        except Exception:
            # Fallback URL construction if Cloudinary utils not available
            cloud = settings.cloudinary_cloud_name or "demo"
            fmt_suffix = f".{format_ext}" if format_ext else ""
            return f"https://res.cloudinary.com/{cloud}/image/upload/c_limit,w_800,q_auto,f_auto/{public_id}{fmt_suffix}"

    def build_thumbnail_url(self, public_id: str, format_ext: Optional[str] = None) -> str:
        """Derive square thumbnail URL for card and grid displays."""
        try:
            import cloudinary.utils

            url, _ = cloudinary.utils.cloudinary_url(
                public_id,
                format=format_ext,
                secure=settings.cloudinary_secure_delivery,
                transformation=[
                    {"width": 300, "height": 300, "crop": "fill", "gravity": "auto"},
                    {"quality": "auto"},
                    {"fetch_format": "auto"},
                ],
            )
            return url
        except Exception:
            cloud = settings.cloudinary_cloud_name or "demo"
            fmt_suffix = f".{format_ext}" if format_ext else ""
            return f"https://res.cloudinary.com/{cloud}/image/upload/c_fill,h_300,w_300,q_auto,f_auto/{public_id}{fmt_suffix}"

    def build_original_url(self, public_id: str, format_ext: Optional[str] = None) -> str:
        """Derive full-resolution original inspection image delivery URL."""
        try:
            import cloudinary.utils

            url, _ = cloudinary.utils.cloudinary_url(
                public_id,
                format=format_ext,
                secure=settings.cloudinary_secure_delivery,
            )
            return url
        except Exception:
            cloud = settings.cloudinary_cloud_name or "demo"
            fmt_suffix = f".{format_ext}" if format_ext else ""
            return f"https://res.cloudinary.com/{cloud}/image/upload/{public_id}{fmt_suffix}"

    def upload_image(
        self,
        image_bytes: bytes,
        public_id: Optional[str] = None,
        folder: Optional[str] = None,
        tags: Optional[List[str]] = None,
        context: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Upload validated image bytes to Cloudinary.

        Args:
            image_bytes: Raw verified image bytes.
            public_id: Optional predetermined public ID.
            folder: Cloudinary directory folder (defaults to settings.cloudinary_folder).
            tags: List of searchable asset tags.
            context: Key-value metadata tags.

        Returns:
            Dict[str, Any]: Parsed Cloudinary upload response payload.

        Raises:
            CloudinaryConfigError: If configuration is missing.
            CloudinaryUploadError: If the upload operation fails.
        """
        self._configure_sdk()

        import cloudinary.uploader

        upload_folder = folder or settings.cloudinary_folder
        upload_tags = tags or ["jaldrishti", "heritage_water_structure"]

        upload_options: Dict[str, Any] = {
            "resource_type": "image",
            "folder": upload_folder,
            "tags": upload_tags,
            "overwrite": False,
            "use_filename": False,
            "unique_filename": True,
        }

        if public_id:
            upload_options["public_id"] = public_id

        if context:
            upload_options["context"] = context

        try:
            file_stream = io.BytesIO(image_bytes)
            # Cloudinary Python SDK handles file-like objects (BytesIO)
            response = cloudinary.uploader.upload(file_stream, **upload_options)

            # Sanitize response to guarantee no sensitive data in returned object
            result = {
                "public_id": response.get("public_id"),
                "asset_id": response.get("asset_id"),
                "format": response.get("format"),
                "resource_type": response.get("resource_type", "image"),
                "width": response.get("width"),
                "height": response.get("height"),
                "bytes": response.get("bytes", len(image_bytes)),
                "created_at": response.get("created_at"),
                "secure_url": response.get("secure_url"),
                "url": response.get("url"),
            }

            # Generate preview url with standard responsive transformations
            if result.get("public_id"):
                result["preview_url"] = self.build_preview_url(
                    result["public_id"], result.get("format")
                )

            return result

        except Exception as e:
            # Mask any internal details, URLs, or potential secrets in the error log
            err_msg = str(e)
            if settings.cloudinary_api_secret and settings.cloudinary_api_secret in err_msg:
                err_msg = err_msg.replace(settings.cloudinary_api_secret, "[MASKED]")
            if settings.cloudinary_api_key and settings.cloudinary_api_key in err_msg:
                err_msg = err_msg.replace(settings.cloudinary_api_key, "[MASKED]")

            logger.error("Cloudinary upload failed: %s", err_msg)
            raise CloudinaryUploadError(f"Cloudinary upload failed: {type(e).__name__}") from e

    def delete_image(self, public_id: str) -> bool:
        """Delete an image asset from Cloudinary by its public ID.

        Args:
            public_id: The storage identifier of the asset to delete.

        Returns:
            bool: True if deletion was confirmed, False if asset was not found.

        Raises:
            CloudinaryConfigError: If configuration is missing.
            CloudinaryDeleteError: If deletion fails due to provider errors.
        """
        self._configure_sdk()

        import cloudinary.uploader

        try:
            res = cloudinary.uploader.destroy(public_id, resource_type="image", invalidate=True)
            status_val = res.get("result", "")
            if status_val == "ok":
                return True
            if status_val == "not found":
                logger.info("Asset %s was already not found in Cloudinary.", public_id)
                return False
            logger.warning("Cloudinary destroy returned unexpected status: %s", status_val)
            return False
        except Exception as e:
            err_msg = str(e)
            logger.error("Cloudinary asset deletion failed for %s: %s", public_id, err_msg)
            raise CloudinaryDeleteError(f"Cloudinary deletion failed: {type(e).__name__}") from e


cloudinary_service = CloudinaryService()
