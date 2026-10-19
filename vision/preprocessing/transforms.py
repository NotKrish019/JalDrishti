"""Versioned preprocessing.

Inference preprocessing (`PREPROCESSING_VERSION`):
    1. Decode, apply EXIF orientation, convert to 8-bit RGB (a copy; the source is never mutated).
    2. Letterbox to a square of `image_size`: scale the long side to fit, pad the rest with the
       ImageNet mean colour. Nothing is cropped, so evidence near an edge is never cut away.
    3. Scale to [0, 1] and normalise with ImageNet mean/std (matching pretrained backbones).

Training applies the same steps, preceded by mild, label-preserving augmentation (see
`build_train_transform`). Validation and test use inference preprocessing only.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Tuple, Union

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

PREPROCESSING_VERSION = "letterbox-rgb-imagenet-v1"
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)
_PAD_RGB = tuple(int(round(m * 255)) for m in IMAGENET_MEAN)

ImageSource = Union[str, Path, bytes, Image.Image, np.ndarray]


class ImageValidationError(ValueError):
    """Raised for inputs that cannot be analysed. `code` is stable and machine-readable."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ImageLimits:
    """Bounds on accepted inputs. Decompression-bomb protection comes from max_pixels."""

    min_side: int = 32
    max_side: int = 12000
    max_pixels: int = 60_000_000
    max_bytes: int = 30 * 1024 * 1024
    allowed_formats: Tuple[str, ...] = ("JPEG", "PNG", "WEBP", "BMP", "TIFF")


def load_image(source: ImageSource, limits: ImageLimits = ImageLimits()) -> Image.Image:
    """Decode and validate an input, returning a new RGB PIL image.

    Accepts a path, raw bytes, a PIL image, or an HxWx3 uint8 RGB array.
    """
    if isinstance(source, np.ndarray):
        if source.ndim != 3 or source.shape[2] != 3 or source.dtype != np.uint8:
            raise ImageValidationError("unsupported_array", "Arrays must be HxWx3 uint8 RGB")
        img = Image.fromarray(source.copy(), "RGB")
        _check_size(img.size, limits)
        return img
    if isinstance(source, Image.Image):
        _check_size(source.size, limits)
        return ImageOps.exif_transpose(source).convert("RGB")

    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.is_file():
            raise ImageValidationError("not_found", "Image file does not exist")
        size = path.stat().st_size
        if size == 0:
            raise ImageValidationError("empty_input", "Image file is empty")
        if size > limits.max_bytes:
            raise ImageValidationError("too_large", f"Image file exceeds {limits.max_bytes} bytes")
        data = path.read_bytes()
    elif isinstance(source, (bytes, bytearray)):
        data = bytes(source)
        if not data:
            raise ImageValidationError("empty_input", "Image payload is empty")
        if len(data) > limits.max_bytes:
            raise ImageValidationError("too_large", f"Image payload exceeds {limits.max_bytes} bytes")
    else:
        raise ImageValidationError("unsupported_input", f"Unsupported input type: {type(source).__name__}")

    try:
        with Image.open(io.BytesIO(data)) as probe:
            fmt = probe.format
            _check_size(probe.size, limits)
        if fmt not in limits.allowed_formats:
            raise ImageValidationError("unsupported_format", f"Unsupported image format: {fmt}")
        with Image.open(io.BytesIO(data)) as im:
            im.load()
            return ImageOps.exif_transpose(im).convert("RGB")
    except ImageValidationError:
        raise
    except Image.DecompressionBombError as exc:
        raise ImageValidationError("too_large", str(exc)) from exc
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise ImageValidationError("unreadable_image", f"Image could not be decoded: {type(exc).__name__}") from exc


def _check_size(size: Tuple[int, int], limits: ImageLimits) -> None:
    w, h = size
    if min(w, h) < limits.min_side:
        raise ImageValidationError("too_small", f"Image is {w}x{h}; minimum side is {limits.min_side}px")
    if max(w, h) > limits.max_side or w * h > limits.max_pixels:
        raise ImageValidationError("too_large", f"Image is {w}x{h}; exceeds configured limits")


def letterbox(img: Image.Image, size: int) -> Image.Image:
    """Fit inside size x size without cropping, padding with the normalisation mean colour."""
    contained = ImageOps.contain(img, (size, size), Image.Resampling.BILINEAR)
    canvas = Image.new("RGB", (size, size), _PAD_RGB)
    canvas.paste(contained, ((size - contained.width) // 2, (size - contained.height) // 2))
    return canvas


def to_model_tensor(img: Image.Image, size: int):
    """Inference preprocessing: letterbox + normalise. Returns a 3 x size x size float tensor."""
    import torch

    arr = np.asarray(letterbox(img, size), dtype=np.float32) / 255.0
    arr = (arr - np.array(IMAGENET_MEAN, dtype=np.float32)) / np.array(IMAGENET_STD, dtype=np.float32)
    return torch.from_numpy(np.ascontiguousarray(arr.transpose(2, 0, 1)))


def build_train_transform(size: int, augment: Optional[Mapping[str, Any]] = None):
    """Mild, label-preserving augmentation followed by inference preprocessing.

    Defaults are deliberately conservative for image-level damage labels: crops keep at least
    80% of the area (so visible evidence is unlikely to be cropped out), rotations are small,
    and colour changes stay within plausible daylight/exposure variation.
    """
    from torchvision.transforms import v2

    a = {
        "min_crop_area": 0.8,
        "hflip": True,
        "rotate_degrees": 8.0,
        "brightness": 0.2,
        "contrast": 0.2,
        "saturation": 0.15,
        "hue": 0.02,
        "jpeg_quality_min": None,
    }
    a.update(dict(augment or {}))
    if not 0.3 <= a["min_crop_area"] <= 1.0:
        raise ValueError("min_crop_area must be in [0.3, 1.0]")

    ops = [v2.RandomResizedCrop(size=size, scale=(a["min_crop_area"], 1.0), ratio=(0.9, 1.1), antialias=True)]
    if a["hflip"]:
        ops.append(v2.RandomHorizontalFlip())
    if a["rotate_degrees"]:
        ops.append(v2.RandomRotation(a["rotate_degrees"], fill=list(_PAD_RGB)))
    ops.append(v2.ColorJitter(a["brightness"], a["contrast"], a["saturation"], a["hue"]))
    if a["jpeg_quality_min"]:
        ops.append(v2.JPEG(quality=(int(a["jpeg_quality_min"]), 95)))
    augment_op = v2.Compose(ops)

    def transform(img: Image.Image):
        # Letterbox first so augmentation works on the same framing inference sees.
        return to_model_tensor(augment_op(letterbox(img, size)), size)

    return transform
