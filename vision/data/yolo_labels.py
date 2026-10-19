"""Validation of YOLO detection labels (`class xc yc w h`, normalised) against their images.

Layout supported (the published Darbhanga Fort crack dataset uses it):

    <root>/<split>/images/*.jpg  +  <root>/<split>/labels/*.txt  (+ labels/classes.txt)
    <root>/<split>/*.jpg                                          (a split with no labels)

Nothing is fixed or rewritten here: every problem is reported so a person can decide.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from vision.data.manifest import IMAGE_EXTENSIONS


@dataclass
class Box:
    class_id: int
    xc: float
    yc: float
    w: float
    h: float

    @property
    def area(self) -> float:
        return self.w * self.h


@dataclass
class LabelCheck:
    image_rel: str
    label_rel: Optional[str]
    boxes: List[Box] = field(default_factory=list)
    problems: List[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.label_rel is None:
            return "no_label_file"
        if self.problems:
            return "invalid"
        return "negative" if not self.boxes else "positive"


def read_classes(labels_dir: Path) -> Optional[List[str]]:
    p = labels_dir / "classes.txt"
    if not p.is_file():
        return None
    return [line.strip() for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_label_file(path: Path, n_classes: Optional[int], tolerance: float = 1e-6) -> tuple[List[Box], List[str]]:
    boxes: List[Box] = []
    problems: List[str] = []
    for i, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 5:
            problems.append(f"line {i}: expected 5 fields, got {len(parts)}")
            continue
        try:
            cls = int(parts[0])
            xc, yc, w, h = (float(v) for v in parts[1:])
        except ValueError:
            problems.append(f"line {i}: non-numeric field")
            continue
        if cls < 0 or (n_classes is not None and cls >= n_classes):
            problems.append(f"line {i}: class id {cls} not in classes.txt")
        if not (w > 0 and h > 0):
            problems.append(f"line {i}: non-positive size")
        lo, hi = -tolerance, 1 + tolerance
        if not all(lo <= v <= hi for v in (xc, yc, w, h)):
            problems.append(f"line {i}: value outside [0, 1]")
        elif xc - w / 2 < lo or xc + w / 2 > hi or yc - h / 2 < lo or yc + h / 2 > hi:
            problems.append(f"line {i}: box extends beyond the image")
        boxes.append(Box(cls, xc, yc, w, h))
    return boxes, problems


def check_split(root: Path, split: str) -> Dict:
    """Pair images with labels for one split directory and validate every label file."""
    split_dir = root / split
    images_dir = split_dir / "images" if (split_dir / "images").is_dir() else split_dir
    labels_dir = split_dir / "labels"
    classes = read_classes(labels_dir) if labels_dir.is_dir() else None
    images = sorted(p for p in images_dir.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS)
    labels = (
        {p.stem: p for p in labels_dir.iterdir() if p.suffix == ".txt" and p.name != "classes.txt"}
        if labels_dir.is_dir() else {}
    )

    checks: List[LabelCheck] = []
    for img in images:
        lab = labels.get(img.stem)
        c = LabelCheck(image_rel=img.relative_to(root).as_posix(),
                       label_rel=lab.relative_to(root).as_posix() if lab else None)
        if lab is not None:
            c.boxes, c.problems = parse_label_file(lab, len(classes) if classes else None)
        checks.append(c)
    image_stems = {p.stem for p in images}
    orphans = sorted(p.relative_to(root).as_posix() for s, p in labels.items() if s not in image_stems)
    return {"split": split, "classes": classes, "checks": checks, "orphan_labels": orphans,
            "has_labels_dir": labels_dir.is_dir()}


def summarise(splits: Sequence[Dict]) -> Dict:
    """Counts and box statistics per split, suitable for the audit report."""
    out = {}
    for s in splits:
        checks: List[LabelCheck] = s["checks"]
        status = Counter(c.status for c in checks)
        areas = sorted(b.area for c in checks for b in c.boxes)
        per_image = Counter(len(c.boxes) for c in checks if c.label_rel is not None)

        def q(p: float) -> Optional[float]:
            return round(areas[min(len(areas) - 1, int(p * (len(areas) - 1)))], 4) if areas else None

        out[s["split"]] = {
            "images": len(checks),
            "label_files": sum(1 for c in checks if c.label_rel) + len(s["orphan_labels"]),
            "classes": s["classes"],
            "status": dict(status),
            "orphan_labels": s["orphan_labels"],
            "boxes": len(areas),
            "boxes_per_image": dict(sorted(per_image.items())),
            "box_area_fraction": {"min": q(0), "p10": q(0.1), "median": q(0.5), "p90": q(0.9), "max": q(1)},
            "boxes_over_half_the_image": sum(1 for a in areas if a > 0.5),
            "invalid_examples": [{"image": c.image_rel, "problems": c.problems[:3]} for c in checks if c.problems][:20],
            "class_counts": dict(Counter(b.class_id for c in checks for b in c.boxes)),
        }
    return out
