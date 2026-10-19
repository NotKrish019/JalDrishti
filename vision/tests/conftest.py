"""Shared fixtures: a small synthetic dataset that exercises every audit path.

No real data and no downloads: images are generated with PIL, so tests run anywhere.
"""

from __future__ import annotations

import io
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _texture(seed: int, size: int = 96) -> Image.Image:
    rng = np.random.default_rng(seed)
    base = rng.integers(90, 170, (size // 8, size // 8, 3), dtype=np.uint8)
    img = Image.fromarray(base).resize((size, size), Image.Resampling.BILINEAR)
    return img


def _crack(img: Image.Image, seed: int) -> Image.Image:
    rng = np.random.default_rng(seed)
    out = img.copy()
    d = ImageDraw.Draw(out)
    x, y = int(rng.integers(5, 30)), 0
    pts = [(x, y)]
    while y < img.height:
        x += int(rng.integers(-6, 7))
        y += int(rng.integers(6, 14))
        pts.append((x, y))
    d.line(pts, fill=(15, 12, 10), width=4)
    return out


@pytest.fixture()
def synthetic_dataset(tmp_path: Path) -> Path:
    """Two label folders plus deliberate edge cases.

    Damaged_images: 14 images with a dark crack-like line (+1 exact copy, +1 re-encoded near copy)
    Background_images: 14 plain textures (+1 grayscale image)
    Edge cases: a corrupt file, an empty file, and one image duplicated across both folders.
    """
    root = tmp_path / "dataset"
    dmg = root / "Damaged_images"
    bg = root / "Background_images"
    dmg.mkdir(parents=True)
    bg.mkdir()
    for i in range(14):
        _crack(_texture(i), i).save(dmg / f"0 ({i}).jpg", quality=92)
        _texture(100 + i).save(bg / f"ND ({i}).jpg", quality=92)
    shutil.copy(dmg / "0 (0).jpg", dmg / "copy_of_0.jpg")  # exact duplicate
    with Image.open(dmg / "0 (1).jpg") as im:  # near duplicate: re-encoded at lower quality
        im.save(dmg / "reencoded_1.jpg", quality=60)
    _texture(200).convert("L").save(bg / "ND (gray).jpg")  # non-RGB mode
    (dmg / "broken.jpg").write_bytes(b"\xff\xd8\xff\xe0 not really a jpeg")
    (bg / "empty.jpg").write_bytes(b"")
    shutil.copy(bg / "ND (3).jpg", dmg / "mislabelled_bg3.jpg")  # same image in both folders
    return root


@pytest.fixture()
def jpeg_bytes() -> bytes:
    buf = io.BytesIO()
    _texture(5, 128).save(buf, "JPEG", quality=90)
    return buf.getvalue()
