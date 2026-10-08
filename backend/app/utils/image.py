"""Utility functions for image inspection without third-party heavy dependencies.

Maintained by Swastik Parmar (Backend / Integration Engineer).
Extracts spatial dimensions from raw JPEG and PNG byte streams deterministically.
"""

import struct
from typing import Optional, Tuple


def get_image_dimensions_from_bytes(data: bytes) -> Optional[Tuple[int, int]]:
    """Extract width and height in pixels from raw PNG or JPEG bytes.

    Args:
        data: Raw image file bytes.

    Returns:
        Optional[Tuple[int, int]]: (width_pixels, height_pixels) or None if unparseable.
    """
    if not data or len(data) < 24:
        return None

    # Check for PNG signature
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        try:
            width, height = struct.unpack(">II", data[16:24])
            if width > 0 and height > 0:
                return (int(width), int(height))
        except struct.error:
            return None

    # Check for JPEG signature (SOI marker 0xFF 0xD8)
    if data.startswith(b"\xff\xd8"):
        try:
            offset = 2
            size = len(data)
            while offset < size:
                if data[offset] != 0xFF:
                    offset += 1
                    continue
                marker = data[offset + 1]
                # SOF (Start of Frame) markers
                if marker in (
                    0xC0,
                    0xC1,
                    0xC2,
                    0xC3,
                    0xC5,
                    0xC6,
                    0xC7,
                    0xC9,
                    0xCA,
                    0xCB,
                    0xCD,
                    0xCE,
                    0xCF,
                ):
                    # Segment: 2 bytes length, 1 byte precision, 2 bytes height, 2 bytes width
                    height, width = struct.unpack(">HH", data[offset + 5 : offset + 9])
                    if width > 0 and height > 0:
                        return (int(width), int(height))
                    break
                else:
                    # Skip segment length
                    if offset + 4 <= size:
                        length = struct.unpack(">H", data[offset + 2 : offset + 4])[0]
                        offset += 2 + length
                    else:
                        break
        except (struct.error, IndexError):
            return None

    return None
