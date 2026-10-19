"""Leakage-safe train/val/test split from an audited manifest.

    python3 scripts/vision/make_splits.py --config vision/configs/classification_pilot.yaml \
        --manifest vision/outputs/audit/manifest.jsonl

Reads the class mapping, seed, ratios and near-duplicate distance from the experiment config,
regroups duplicates, assigns whole groups to splits, verifies there is no leakage, and writes:

    <config data.manifest>   (default vision/outputs/audit/manifest_split.jsonl)
    split_report.json        class counts per split, exclusions and reasons
    exclusions.jsonl         one line per excluded image with its reason
    split_<name>.txt         relative paths per split

Optional --groups CSV (sample rel_path,group_key) adds capture-metadata grouping, e.g. site or
session, so related photographs stay in the same split.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from vision.data.duplicates import find_duplicates  # noqa: E402
from vision.data.manifest import read_manifest, write_manifest  # noqa: E402
from vision.data.splits import SPLITS, check_leakage, make_group_splits  # noqa: E402
from vision.training.config import load_config  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Create leakage-safe splits")
    ap.add_argument("--config", required=True)
    ap.add_argument("--manifest", default="vision/outputs/audit/manifest.jsonl", help="audited manifest")
    ap.add_argument("--groups", default=None, help="optional CSV of rel_path,group_key")
    args = ap.parse_args()

    cfg = load_config(args.config)
    records = read_manifest(cfg.resolve(args.manifest))
    dup = find_duplicates(records, max_distance=cfg.data.near_duplicate_distance)

    extra = None
    if args.groups:
        by_path = {r.rel_path: r.sample_id for r in records}
        extra = {}
        with open(args.groups, newline="", encoding="utf-8") as f:
            for row in csv.reader(f):
                if len(row) >= 2 and row[0] in by_path:
                    extra[by_path[row[0]]] = row[1]

    result = make_group_splits(
        records, cfg.labels.folder_to_class, cfg.data.split_ratios, seed=cfg.data.split_seed, extra_groups=extra
    )
    problems = check_leakage(records)
    if problems:
        for p in problems[:20]:
            print("LEAKAGE:", p, file=sys.stderr)
        return 1

    out_manifest = cfg.resolve(cfg.data.manifest)
    write_manifest(records, out_manifest)
    out_dir = out_manifest.parent
    report = {
        **result.to_dict(),
        "near_duplicate_distance": cfg.data.near_duplicate_distance,
        "duplicate_groups": len(dup.groups),
        "cross_label_duplicate_groups": len(dup.label_conflicts),
        "metadata_grouping": bool(extra),
        "leakage_check": "passed",
        "limitations": [
            "All images come from one site; this split cannot measure cross-site generalisation."
            if not extra else "Grouped by supplied metadata.",
            "Related-but-different photographs of the same wall cannot be detected by hashing.",
        ],
    }
    (out_dir / "split_report.json").write_text(json.dumps(report, indent=2))
    with open(out_dir / "exclusions.jsonl", "w", encoding="utf-8") as f:
        for r in records:
            if r.exclusion_reason:
                f.write(json.dumps({"rel_path": r.rel_path, "reason": r.exclusion_reason}) + "\n")
    for s in SPLITS:
        paths = sorted(r.rel_path for r in records if r.split == s)
        (out_dir / f"split_{s}.txt").write_text("\n".join(paths) + ("\n" if paths else ""))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
