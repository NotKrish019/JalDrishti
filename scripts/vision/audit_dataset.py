"""Dataset audit: manifest, duplicates, annotation inventory and supervision assessment.

Owner: Krish (Computer Vision / AI)

    python3 scripts/vision/audit_dataset.py --data-dir Darbhanga_Fort/Darbhanga_Fort \
        --out vision/outputs/audit

Writes (all paths inside are relative to the dataset root):
    manifest.jsonl       one validated record per image
    duplicates.json      exact (SHA-256) and near (dHash) duplicate groups, label conflicts
    annotations.json     every file that could be supervision beyond folder names
    audit_report.json    summary counts and the supervision assessment
    audit_report.md      the same, for people

Re-running on the same files produces identical outputs (except the timestamp).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from vision.data.duplicates import DEFAULT_NEAR_DISTANCE, find_duplicates  # noqa: E402
from vision.data.manifest import ImageRecord, build_manifest, find_annotation_files, write_manifest  # noqa: E402

CANDIDATE_ROOTS = [
    "data/raw/darbhanga_crack/Crack Data-Darbhanga Fort",  # extracted from DrabhangaDataset.zip
    "Darbhanga_Fort/Darbhanga_Fort",
    "Darbhanga_Fort",
    "data/raw/Darbhanga_Fort/Darbhanga_Fort",
    "data/raw/Darbhanga_Fort",
]


def find_dataset_dir(provided_path: Optional[str] = None) -> Optional[Path]:
    """Return the dataset root, or None if it is not present on this machine."""
    if provided_path:
        p = Path(provided_path)
        return p if p.is_dir() else None
    for c in CANDIDATE_ROOTS:
        p = PROJECT_ROOT / c
        if any((p / d).is_dir() for d in ("Damaged_images", "Background_images", "train")):
            return p
    return None


def calculate_file_hash(filepath: Path, chunk_size: int = 65536) -> str:
    """SHA-256 of a file's bytes (exact-duplicate identity)."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def assess_supervision(annotations: Dict[str, List[str]], folder_counts: Dict[str, int]) -> Dict[str, Any]:
    """What learning tasks the files on disk could support, before anyone verifies semantics."""
    has_boxes = bool(annotations.get("yolo_txt") or annotations.get("voc_xml") or annotations.get("json"))
    has_masks = bool(annotations.get("mask_image"))
    return {
        "image_level_folders": sorted(folder_counts),
        "object_detection": "candidate files present - must be validated" if has_boxes else "not supported: no box annotations found",
        "segmentation": "candidate mask files present - must be validated" if has_masks else "not supported: no masks found",
        "image_classification": (
            "possible only if the folder labels are verified to mean a defined, observable condition"
            if len(folder_counts) >= 2 else "not supported: fewer than two label folders"
        ),
        "note": "Folder names are provenance, not verified classes. Review contact sheets before training.",
    }


def audit_dataset(root_dir: Path, near_distance: int = DEFAULT_NEAR_DISTANCE) -> Dict[str, Any]:
    """Audit root_dir and return {summary, records, duplicates, annotations}."""
    root_dir = Path(root_dir)
    records: List[ImageRecord] = list(build_manifest(root_dir))
    dup = find_duplicates(records, max_distance=near_distance)
    annotations = find_annotation_files(root_dir)

    folder_counts = Counter(str(r.folder_label) for r in records)
    readable = [r for r in records if r.readable]
    summary = {
        "total_images": len(records),
        "readable_images": len(readable),
        "unreadable_images": len(records) - len(readable),
        "unreadable": [{"rel_path": r.rel_path, "error": r.error} for r in records if not r.readable],
        "images_per_folder": dict(sorted(folder_counts.items())),
        "readable_per_folder": dict(sorted(Counter(str(r.folder_label) for r in readable).items())),
        "formats": dict(Counter(str(r.format) for r in readable).most_common()),
        "modes": dict(Counter(str(r.mode) for r in readable).most_common()),
        "resolutions": [
            {"width": w, "height": h, "count": c}
            for (w, h), c in Counter((r.width, r.height) for r in readable).most_common(10)
        ],
        "quality_flags": dict(Counter(f for r in records for f in r.flags).most_common()),
        "exact_duplicate_groups": len(dup.exact_groups),
        "exact_duplicate_redundant_files": dup.exact_duplicate_files,
        "near_duplicate_pairs": len(dup.near_pairs),
        "duplicate_groups_total": len(dup.groups),
        "cross_label_duplicate_groups": len(dup.label_conflicts),
        "duplicate_method": dup.method,
        "annotation_files": {k: len(v) for k, v in annotations.items()},
        "supervision": assess_supervision(annotations, dict(folder_counts)),
    }
    return {"summary": summary, "records": records, "duplicates": dup, "annotations": annotations}


def _markdown(summary: Dict[str, Any], dataset_label: str) -> str:
    s = summary
    lines = [
        "# Dataset audit",
        "",
        f"- Dataset: `{dataset_label}`",
        f"- Generated (UTC): {s['generated_utc']}",
        f"- Images: {s['total_images']} ({s['readable_images']} readable, {s['unreadable_images']} unreadable)",
        "",
        "## Per folder",
        "",
        "| Folder | Images | Readable |",
        "| --- | ---: | ---: |",
    ]
    for k, v in s["images_per_folder"].items():
        lines.append(f"| {k} | {v} | {s['readable_per_folder'].get(k, 0)} |")
    lines += ["", "## Formats, modes, resolutions", "", f"- Formats: {s['formats']}", f"- Modes: {s['modes']}"]
    lines += [f"- {r['width']}x{r['height']}: {r['count']}" for r in s["resolutions"]]
    lines += [
        "", "## Quality flags", "", f"{s['quality_flags'] or 'none'}",
        "", "## Duplicates", "",
        f"- Exact groups: {s['exact_duplicate_groups']} ({s['exact_duplicate_redundant_files']} redundant files)",
        f"- Near-duplicate pairs: {s['near_duplicate_pairs']}",
        f"- Groups spanning different folders (need review): {s['cross_label_duplicate_groups']}",
        f"- Method: {s['duplicate_method']}",
        "", "## Annotations", "", f"- Files found: {s['annotation_files'] or 'none'}",
        "", "## Supervision assessment", "",
    ]
    lines += [f"- **{k}**: {v}" for k, v in s["supervision"].items()]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit the vision dataset")
    ap.add_argument("--data-dir", default=None, help="dataset root (folders of images)")
    ap.add_argument("--out", default="vision/outputs/audit", help="output directory")
    ap.add_argument("--near-distance", type=int, default=DEFAULT_NEAR_DISTANCE)
    args = ap.parse_args()

    root = find_dataset_dir(args.data_dir)
    if root is None:
        print("ERROR: dataset not found. Pass --data-dir or place it at one of:", file=sys.stderr)
        for c in CANDIDATE_ROOTS:
            print(f"  {c}", file=sys.stderr)
        return 2

    out = Path(args.out)
    out = out if out.is_absolute() else PROJECT_ROOT / out
    out.mkdir(parents=True, exist_ok=True)
    print(f"Auditing {root.name} ...")
    result = audit_dataset(root, args.near_distance)
    summary = result["summary"]
    summary["generated_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        label = root.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        label = root.name

    write_manifest(result["records"], out / "manifest.jsonl")
    (out / "duplicates.json").write_text(json.dumps(result["duplicates"].to_dict(), indent=2))
    (out / "annotations.json").write_text(json.dumps(result["annotations"], indent=2))
    (out / "audit_report.json").write_text(json.dumps({"dataset": label, **summary}, indent=2))
    (out / "audit_report.md").write_text(_markdown(summary, label))
    print(_markdown(summary, label))
    print(f"Wrote manifest and reports to {out.relative_to(PROJECT_ROOT) if out.is_relative_to(PROJECT_ROOT) else out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
