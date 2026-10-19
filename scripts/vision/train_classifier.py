"""Train the image-classification pilot.

    python3 scripts/vision/train_classifier.py --config vision/configs/classification_pilot.yaml

Refuses to run while `labels.verified` is false. `--allow-unverified-labels` exists only to
smoke-test the pipeline end to end; the resulting checkpoint is marked `label_status:
unverified` and the predictor warns on every result. Override epochs / batch limits for a
bounded first run with --epochs and --max-train-batches.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from vision.training.config import ConfigError, load_config  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--allow-unverified-labels", action="store_true",
                    help="pipeline smoke test only; checkpoint is marked unverified")
    ap.add_argument("--epochs", type=int, default=None)
    ap.add_argument("--max-train-batches", type=int, default=None)
    ap.add_argument("--device", default=None)
    ap.add_argument("--no-pretrained", action="store_true", help="random initialisation (no weight download)")
    ap.add_argument("--run-name", default=None)
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.epochs:
        cfg.train.epochs = args.epochs
    if args.max_train_batches:
        cfg.train.max_train_batches = args.max_train_batches
    if args.device:
        cfg.train.device = args.device
    if args.no_pretrained:
        cfg.model.pretrained = False
    try:
        cfg.validate(allow_unverified_labels=args.allow_unverified_labels)
    except ConfigError as exc:
        print(f"CONFIG REJECTED: {exc}", file=sys.stderr)
        return 2

    from vision.training.classifier import train

    run_dir = train(cfg, allow_unverified_labels=args.allow_unverified_labels, run_name=args.run_name)
    print(f"run complete: {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
