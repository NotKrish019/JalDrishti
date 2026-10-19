"""Input validation and versioned preprocessing."""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from vision.preprocessing.transforms import (
    IMAGENET_MEAN,
    ImageLimits,
    ImageValidationError,
    letterbox,
    load_image,
)

torch = pytest.importorskip("torch")
from vision.preprocessing.transforms import build_train_transform, to_model_tensor  # noqa: E402


def test_load_image_from_all_supported_sources(jpeg_bytes: bytes, tmp_path: Path) -> None:
    p = tmp_path / "a.jpg"
    p.write_bytes(jpeg_bytes)
    arr = np.zeros((40, 50, 3), dtype=np.uint8)
    for src in (p, str(p), jpeg_bytes, Image.open(io.BytesIO(jpeg_bytes)), arr):
        img = load_image(src)
        assert img.mode == "RGB"


def test_grayscale_and_rgba_are_converted_to_rgb() -> None:
    for mode in ("L", "RGBA", "P"):
        buf = io.BytesIO()
        Image.new(mode, (64, 48)).save(buf, "PNG")
        assert load_image(buf.getvalue()).mode == "RGB"


@pytest.mark.parametrize(
    "payload,code",
    [
        (b"", "empty_input"),
        (b"definitely not an image", "unreadable_image"),
        (12345, "unsupported_input"),
        (np.zeros((10, 10), dtype=np.uint8), "unsupported_array"),
    ],
)
def test_invalid_inputs_raise_with_stable_codes(payload, code) -> None:
    with pytest.raises(ImageValidationError) as exc:
        load_image(payload)
    assert exc.value.code == code


def test_size_limits() -> None:
    buf = io.BytesIO()
    Image.new("RGB", (20, 20)).save(buf, "PNG")
    with pytest.raises(ImageValidationError) as exc:
        load_image(buf.getvalue())
    assert exc.value.code == "too_small"
    buf = io.BytesIO()
    Image.new("RGB", (400, 300)).save(buf, "PNG")
    with pytest.raises(ImageValidationError) as exc:
        load_image(buf.getvalue(), ImageLimits(max_side=200))
    assert exc.value.code == "too_large"
    with pytest.raises(ImageValidationError) as exc:
        load_image(b"x" * 100, ImageLimits(max_bytes=10))
    assert exc.value.code == "too_large"


def test_unsupported_format_rejected() -> None:
    buf = io.BytesIO()
    Image.new("RGB", (64, 64)).save(buf, "GIF")
    with pytest.raises(ImageValidationError) as exc:
        load_image(buf.getvalue())
    assert exc.value.code == "unsupported_format"


def test_missing_file() -> None:
    with pytest.raises(ImageValidationError) as exc:
        load_image("does/not/exist.jpg")
    assert exc.value.code == "not_found"


def test_source_is_not_mutated() -> None:
    arr = np.full((64, 80, 3), 7, dtype=np.uint8)
    before = arr.copy()
    img = load_image(arr)
    to_model_tensor(img, 32)
    assert np.array_equal(arr, before)
    pil = Image.new("RGB", (64, 64), (10, 20, 30))
    load_image(pil)
    assert pil.getpixel((0, 0)) == (10, 20, 30) and pil.mode == "RGB"


def test_letterbox_keeps_all_content_and_pads_with_mean() -> None:
    img = Image.new("RGB", (200, 100), (255, 0, 0))
    out = letterbox(img, 64)
    assert out.size == (64, 64)
    pad = tuple(int(round(m * 255)) for m in IMAGENET_MEAN)
    assert out.getpixel((32, 2)) == pad  # padding band above the content
    assert out.getpixel((32, 32))[0] > 200  # content preserved, not cropped


def test_model_tensor_shape_and_normalisation() -> None:
    t = to_model_tensor(Image.new("RGB", (100, 60), (124, 116, 104)), 48)
    assert t.shape == (3, 48, 48)
    assert t.dtype == torch.float32
    assert float(t.abs().max()) < 0.05  # ImageNet mean colour normalises to ~0 everywhere


def test_inference_preprocessing_is_deterministic(jpeg_bytes: bytes) -> None:
    a = to_model_tensor(load_image(jpeg_bytes), 64)
    b = to_model_tensor(load_image(jpeg_bytes), 64)
    assert torch.equal(a, b)


def test_train_transform_shape_and_bounds() -> None:
    tf = build_train_transform(64)
    out = tf(Image.new("RGB", (120, 90), (100, 110, 120)))
    assert out.shape == (3, 64, 64)
    with pytest.raises(ValueError):
        build_train_transform(64, {"min_crop_area": 0.1})
