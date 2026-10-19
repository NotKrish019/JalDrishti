"""Streaming image manifest.

Walks a dataset root, validates every image one at a time (never the whole dataset in
memory), and records what can be verified about it. Paths are stored relative to the
dataset root with POSIX separators, so manifests carry no private machine paths.

A folder name is recorded as `folder_label` only: it is *where the file was found*, not
a verified class. Whether a folder label is valid supervision for a task is decided
separately and recorded in the experiment configuration (`labels_verified`).
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

from PIL import Image, UnidentifiedImageError

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
ANNOTATION_EXTENSIONS = {".txt", ".json", ".xml", ".yaml", ".yml", ".csv"}

# Thresholds used to raise data-quality flags (not to reject images).
MIN_SIDE = 64
MAX_SIDE = 12000
EXTREME_ASPECT = 3.0
HASH_CHUNK = 1 << 16


@dataclass
class ImageRecord:
    """Everything the audit can verify about one image file."""

    sample_id: str
    rel_path: str
    folder_label: Optional[str]
    file_size: int
    sha256: str
    readable: bool
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    mode: Optional[str] = None
    channels: Optional[int] = None
    dhash: Optional[str] = None
    error: Optional[str] = None
    flags: List[str] = field(default_factory=list)
    # Filled in later by duplicate analysis and split generation.
    duplicate_group: Optional[str] = None
    split: Optional[str] = None
    exclusion_reason: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(HASH_CHUNK):
            h.update(chunk)
    return h.hexdigest()


def _stable_id(rel_path: str) -> str:
    """Identifier derived from the relative path: stable across re-runs and machines."""
    return "s_" + hashlib.sha1(rel_path.encode("utf-8")).hexdigest()[:12]


def dhash_hex(img: Image.Image, size: int = 8) -> str:
    """64-bit difference hash: robust to rescaling and re-encoding, used for near-duplicates."""
    small = img.convert("L").resize((size + 1, size), Image.Resampling.LANCZOS)
    px = small.tobytes()
    bits = 0
    for row in range(size):
        for col in range(size):
            left = px[row * (size + 1) + col]
            right = px[row * (size + 1) + col + 1]
            bits = (bits << 1) | (1 if left > right else 0)
    return f"{bits:016x}"


def iter_image_paths(root: Path) -> Iterator[Path]:
    """All supported image files under root, in a deterministic order."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            p = Path(dirpath) / name
            if p.suffix.lower() in IMAGE_EXTENSIONS:
                yield p


def inspect_image(path: Path, root: Path) -> ImageRecord:
    """Validate a single image file. Never raises for bad image content; records the error."""
    rel = path.relative_to(root).as_posix()
    parts = Path(rel).parts
    folder_label = parts[0] if len(parts) > 1 else None
    size = path.stat().st_size
    record = ImageRecord(
        sample_id=_stable_id(rel),
        rel_path=rel,
        folder_label=folder_label,
        file_size=size,
        sha256=_sha256(path),
        readable=False,
    )
    if size == 0:
        record.error = "empty file"
        record.flags.append("empty_file")
        return record
    try:
        with Image.open(path) as im:
            im.verify()
        # verify() leaves the image unusable; reopen and fully decode to catch truncation.
        with Image.open(path) as im:
            im.load()
            record.width, record.height = im.size
            record.format = im.format
            record.mode = im.mode
            record.channels = len(im.getbands())
            record.dhash = dhash_hex(im)
        record.readable = True
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        record.error = f"{type(exc).__name__}: {exc}"
        record.flags.append("unreadable")
        return record

    w, h = record.width or 0, record.height or 0
    if min(w, h) < MIN_SIDE:
        record.flags.append("very_small")
    if max(w, h) > MAX_SIDE:
        record.flags.append("very_large")
    if max(w, h) / max(1, min(w, h)) > EXTREME_ASPECT:
        record.flags.append("extreme_aspect_ratio")
    if record.mode not in ("RGB",):
        record.flags.append(f"mode_{record.mode}")
    return record


def build_manifest(root: Path | str) -> Iterator[ImageRecord]:
    """Yield one validated record per image under root (streaming)."""
    root = Path(root)
    if not root.is_dir():
        raise FileNotFoundError(f"Dataset root does not exist or is not a directory: {root}")
    for path in iter_image_paths(root):
        yield inspect_image(path, root)


def find_annotation_files(root: Path | str) -> Dict[str, List[str]]:
    """Locate anything that could be supervision beyond folder names, grouped by kind.

    Kinds: yolo_txt, json (possibly COCO), voc_xml, tabular, yaml, mask_image (images that
    live in a directory whose name suggests masks/labels).
    """
    root = Path(root)
    found: Dict[str, List[str]] = {}

    def add(kind: str, p: Path) -> None:
        found.setdefault(kind, []).append(p.relative_to(root).as_posix())

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        lower_dir = Path(dirpath).name.lower()
        for name in sorted(filenames):
            p = Path(dirpath) / name
            ext = p.suffix.lower()
            if name == ".gitkeep":
                continue
            if ext == ".txt":
                add("yolo_txt", p)
            elif ext == ".json":
                add("json", p)
            elif ext == ".xml":
                add("voc_xml", p)
            elif ext == ".csv":
                add("tabular", p)
            elif ext in (".yaml", ".yml"):
                add("yaml", p)
            elif ext in IMAGE_EXTENSIONS and any(k in lower_dir for k in ("mask", "label", "annot", "segment")):
                add("mask_image", p)
    return found


def write_manifest(records: Iterable[ImageRecord], path: Path | str) -> int:
    """Write records as JSON Lines. Returns the number written."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r.to_dict(), sort_keys=True) + "\n")
            n += 1
    return n


def read_manifest(path: Path | str) -> List[ImageRecord]:
    records: List[ImageRecord] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(ImageRecord(**json.loads(line)))
    return records
