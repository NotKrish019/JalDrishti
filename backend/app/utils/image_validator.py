"""Strict image upload validation with bounded streaming and content decodability.

Maintained by Swastik Parmar (Backend / Integration Engineer).
Validates image files by verifying:
1. File size within bounded memory limits (streaming read defense against memory exhaustion).
2. Non-empty file payloads.
3. Actual image header and stream decodability via Pillow (does NOT trust MIME headers or extensions).
4. Whitelisted heritage-safe image formats (JPEG, PNG, WEBP).
5. Valid non-zero spatial dimensions.
"""

import io
import logging
from typing import List, Optional, Tuple
from fastapi import UploadFile

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class ImageValidationError(Exception):
    """Base exception for image validation failures."""
    pass


class ImageEmptyError(ImageValidationError):
    """Raised when an empty (0-byte) image upload is received."""
    pass


class ImageSizeLimitError(ImageValidationError):
    """Raised when an uploaded image exceeds the maximum permitted size."""
    pass


class ImageFormatError(ImageValidationError):
    """Raised when an uploaded file is not an allowed image format."""
    pass


class ImageDecodeError(ImageValidationError):
    """Raised when image bytes cannot be decoded or are corrupted."""
    pass


async def read_and_validate_image_upload(
    upload_file: UploadFile,
    max_size_bytes: Optional[int] = None,
    allowed_formats: Optional[List[str]] = None,
) -> Tuple[bytes, str, int, int]:
    """Perform bounded streaming read and strict decodability validation.

    Args:
        upload_file: Incoming FastAPI UploadFile instance.
        max_size_bytes: Maximum allowed file size in bytes (defaults to settings.max_upload_size_bytes).
        allowed_formats: Permitted format strings (defaults to settings.allowed_image_formats).

    Returns:
        Tuple[bytes, str, int, int]: (verified_bytes, normalized_format, width, height)

    Raises:
        ImageEmptyError: If 0 bytes are read.
        ImageSizeLimitError: If payload exceeds max_size_bytes.
        ImageFormatError: If the verified format is not in allowed_formats.
        ImageDecodeError: If content cannot be parsed as a valid image.
    """
    limit = max_size_bytes or settings.max_upload_size_bytes
    formats = [f.lower() for f in (allowed_formats or settings.allowed_image_formats)]
    # Normalize aliases (e.g. 'jpg' -> 'jpeg')
    normalized_allowed = set()
    for fmt in formats:
        normalized_allowed.add("jpeg" if fmt == "jpg" else fmt)

    # 1. Bounded streaming read to protect against memory exhaustion
    buffer = bytearray()
    chunk_size = 64 * 1024  # 64 KB chunks
    total_read = 0

    while True:
        chunk = await upload_file.read(chunk_size)
        if not chunk:
            break
        total_read += len(chunk)
        if total_read > limit:
            max_mb = limit / (1024 * 1024)
            raise ImageSizeLimitError(
                f"File size exceeds maximum allowed limit of {max_mb:.1f} MB ({limit} bytes)."
            )
        buffer.extend(chunk)

    data = bytes(buffer)

    # 2. Check for empty payload
    if len(data) == 0:
        raise ImageEmptyError("Uploaded file is empty (0 bytes).")

    # 3. Content decodability check via Pillow
    try:
        from PIL import Image, UnidentifiedImageError

        img_io = io.BytesIO(data)
        try:
            with Image.open(img_io) as img:
                detected_format = (img.format or "").lower()
                if detected_format == "jpg":
                    detected_format = "jpeg"

                width, height = img.size

                # Verify image integrity
                img.verify()

        except (UnidentifiedImageError, SyntaxError, ValueError) as err:
            logger.warning("Image decoding failed for upload '%s': %s", upload_file.filename, err)
            raise ImageDecodeError("Corrupted or undecodable image file.") from err
        except Exception as err:
            logger.warning("Unexpected error decoding image '%s': %s", upload_file.filename, err)
            raise ImageDecodeError(f"Corrupted or undecodable image file: {err}") from err

    except ImportError:
        # Fallback to internal binary header decoder if Pillow is missing
        logger.warning("Pillow not available; falling back to binary header parser.")
        from backend.app.utils.image import get_image_dimensions_from_bytes
        dims = get_image_dimensions_from_bytes(data)
        if dims is None:
            raise ImageDecodeError("Corrupted or undecodable image file.")
        width, height = dims
        detected_format = "jpeg" if data.startswith(b"\xff\xd8") else "png"

    # 4. Format validation against whitelist
    if detected_format not in normalized_allowed:
        allowed_str = ", ".join(sorted(normalized_allowed))
        raise ImageFormatError(
            f"Unsupported image format '{detected_format}'. Supported formats: {allowed_str}."
        )

    # 5. Sanity check dimensions
    if width <= 0 or height <= 0:
        raise ImageDecodeError("Invalid image dimensions extracted (must be > 0x0 pixels).")

    return data, detected_format, width, height
