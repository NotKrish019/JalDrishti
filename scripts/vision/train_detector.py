"""Train the crack-detection pilot.

    python3 scripts/vision/train_detector.py --config vision/configs/detection_pilot.yaml
    # bounded first run:
    python3 scripts/vision/train_detector.py --config ... --epochs 1 --max-train-batches 20 --max-val-images 64
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from vision.training.config import ConfigError  # noqa: E402
from vision.training.detection import load_detection_config, train_detector  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--epochs", type=int)
    ap.add_argument("--max-train-batches", type=int)
    ap.add_argument("--max-val-images", type=int)
    ap.add_argument("--device")
    ap.add_argument("--run-name")
    ap.add_argument("--allow-unverified-labels", action="store_true")
    args = ap.parse_args()
    cfg = load_detection_config(args.config)
    for k in ("epochs", "max_train_batches", "max_val_images", "device"):
        v = getattr(args, k)
        if v is not None:
            setattr(cfg, k, v)
    try:
        cfg.validate(args.allow_unverified_labels)
    except ConfigError as exc:
        print(f"CONFIG REJECTED: {exc}", file=sys.stderr)
        return 2
    run = train_detector(cfg, args.allow_unverified_labels, args.run_name)
    print(f"run complete: {run}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
