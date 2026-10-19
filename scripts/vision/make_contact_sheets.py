"""Contact sheets for label review: a deterministic sample of each folder in one image.

    python3 scripts/vision/make_contact_sheets.py --data-dir Darbhanga_Fort/Darbhanga_Fort \
        --manifest vision/outputs/audit/manifest.jsonl --per-folder 48

Writes vision/outputs/audit/contact_<folder>.jpg. Use them to decide and write down what each
folder label asserts (labels.semantics in the experiment config) before training.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from vision.data.contact_sheet import make_contact_sheet, sample_by_folder  # noqa: E402
from vision.data.manifest import read_manifest  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--manifest", default="vision/outputs/audit/manifest.jsonl")
    ap.add_argument("--out", default="vision/outputs/audit")
    ap.add_argument("--per-folder", type=int, default=48)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    root = Path(args.data_dir)
    out = Path(args.out)
    out = out if out.is_absolute() else PROJECT_ROOT / out
    records = read_manifest(args.manifest if Path(args.manifest).is_absolute() else PROJECT_ROOT / args.manifest)
    for folder, sample in sample_by_folder(records, args.per_folder, args.seed).items():
        path = make_contact_sheet(root, sample, out / f"contact_{folder}.jpg", title=f"{folder}: {len(sample)} sampled")
        print(f"wrote {path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
