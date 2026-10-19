"""Contact sheets for reviewing what a folder label actually contains.

A deterministic sample of each folder is tiled into one image with filenames underneath, so a
reviewer can judge label semantics (e.g. does `Background_images` mean "no damage", "no
crack", or something else?) before any label is trusted as supervision.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Dict, List, Sequence

from PIL import Image, ImageDraw, ImageOps

from vision.data.manifest import ImageRecord


def sample_by_folder(records: Sequence[ImageRecord], per_folder: int, seed: int = 7) -> Dict[str, List[ImageRecord]]:
    groups: Dict[str, List[ImageRecord]] = {}
    for r in records:
        if r.readable:
            groups.setdefault(str(r.folder_label), []).append(r)
    rng = random.Random(seed)
    out = {}
    for label in sorted(groups):
        recs = sorted(groups[label], key=lambda x: x.rel_path)
        out[label] = rng.sample(recs, min(per_folder, len(recs)))
    return out


def make_contact_sheet(
    root: Path | str,
    records: Sequence[ImageRecord],
    out_path: Path | str,
    columns: int = 6,
    thumb: int = 200,
    title: str = "",
) -> Path:
    """Write a grid of thumbnails (letterboxed, captioned with relative path) to out_path."""
    root = Path(root)
    rows = max(1, -(-len(records) // columns))
    caption = 28
    header = 36 if title else 0
    sheet = Image.new("RGB", (columns * thumb, header + rows * (thumb + caption)), (24, 22, 20))
    draw = ImageDraw.Draw(sheet)
    if title:
        draw.text((10, 10), title, fill=(235, 225, 210))
    for i, rec in enumerate(records):
        x = (i % columns) * thumb
        y = header + (i // columns) * (thumb + caption)
        with Image.open(root / rec.rel_path) as im:
            tile = ImageOps.contain(ImageOps.exif_transpose(im).convert("RGB"), (thumb - 8, thumb - 8))
        sheet.paste(tile, (x + (thumb - tile.width) // 2, y + (thumb - tile.height) // 2))
        name = rec.rel_path.split("/")[-1]
        draw.text((x + 6, y + thumb + 6), name[:30], fill=(200, 190, 175))
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=88)
    return out_path
