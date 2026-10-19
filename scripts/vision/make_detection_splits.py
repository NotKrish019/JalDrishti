"""Leakage-safe re-split of the YOLO crack dataset.

    python3 scripts/vision/make_detection_splits.py --config vision/configs/detection_pilot.yaml \
        --manifest vision/outputs/audit/manifest.jsonl

The published train/val/test folders are NOT used as splits: the audit found the same
photographs (exact and photometric near-duplicates) in more than one of them, and the published
test folder has no labels. Instead every labelled image is regrouped by duplicate group and
assigned whole to train/val/test (70/15/15, stratified by crack vs background).

Duplicate copies are kept in train (they are independently labelled photometric variants) but
only one representative is kept in val and test, so evaluation counts each photograph once.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from vision.data.duplicates import find_duplicates  # noqa: E402
from vision.data.manifest import read_manifest, write_manifest  # noqa: E402
from vision.data.splits import SPLITS, check_leakage, make_group_splits  # noqa: E402
from vision.training.detection import load_detection_config, load_targets  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--manifest", default="vision/outputs/audit/manifest.jsonl")
    ap.add_argument("--seed", type=int, default=1337)
    ap.add_argument("--near-distance", type=int, default=6)
    args = ap.parse_args()

    cfg = load_detection_config(args.config)
    root = cfg.resolve(cfg.dataset_root)
    records = read_manifest(cfg.resolve(args.manifest))
    find_duplicates(records, max_distance=args.near_distance)

    status = {}
    for r in records:
        t = load_targets(root, r, len(cfg.classes), cfg.negatives_without_label_file) if r.readable else None
        status[r.sample_id] = None if t is None else ("crack" if len(t[0]) else "background")

    result = make_group_splits(records, lambda r: status.get(r.sample_id), seed=args.seed, keep_duplicates_in=("train",))
    # Copies kept in train share a group but sit in one split, so any reported problem is real leakage.
    cross = check_leakage(records)
    if cross:
        for p in cross[:20]:
            print("LEAKAGE:", p, file=sys.stderr)
        return 1

    out = cfg.resolve(cfg.manifest)
    write_manifest(records, out)
    reasons = Counter(r.exclusion_reason.split(":")[0] for r in records if r.exclusion_reason)
    unlabelled_by_folder = Counter(r.rel_path.split("/")[0] for r in records if r.exclusion_reason == "unmapped_label")
    report = {
        **result.to_dict(),
        "images_per_split": dict(Counter(r.split for r in records if r.split)),
        "exclusion_reasons": dict(reasons),
        "unlabelled_excluded_by_source_folder": dict(unlabelled_by_folder),
        "duplicates_kept_in": ["train"],
        "leakage_check": "passed (no duplicate group or identical content shared between splits)",
        "note": "published folder split ignored; see script docstring",
    }
    (out.parent / "detection_split_report.json").write_text(json.dumps(report, indent=2))
    for s in SPLITS:
        (out.parent / f"detection_split_{s}.txt").write_text(
            "\n".join(sorted(r.rel_path for r in records if r.split == s)) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
