"""Evaluate a trained classifier checkpoint on one split.

    python3 scripts/vision/evaluate_classifier.py --checkpoint <run_dir>/model.pt \
        --config vision/configs/classification_pilot.yaml --split val
    # once model and threshold are final:
    python3 scripts/vision/evaluate_classifier.py ... --split test

Uses the decision threshold stored in the checkpoint (chosen on validation during training);
nothing is re-tuned here. Writes <run_dir>/eval_<split>.json and error-analysis contact sheets
(eval_<split>_<TP|TN|FP|FN>.jpg) next to the checkpoint.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from vision.data.contact_sheet import make_contact_sheet  # noqa: E402
from vision.data.manifest import read_manifest  # noqa: E402
from vision.inference.predictor import ImageClassifierPredictor  # noqa: E402
from vision.metrics.classification import classification_report  # noqa: E402
from vision.training.classifier import records_for_split  # noqa: E402
from vision.training.config import load_config  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--split", choices=["val", "test"], default="val")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--examples", type=int, default=24, help="images per error-analysis sheet")
    args = ap.parse_args()

    cfg = load_config(args.config)
    ckpt = Path(args.checkpoint)
    predictor = ImageClassifierPredictor.from_checkpoint(ckpt, device=args.device)
    meta = predictor.meta
    classes = meta["classes"]
    if classes != cfg.labels.classes:
        print(f"class mismatch: checkpoint {classes} vs config {cfg.labels.classes}", file=sys.stderr)
        return 2

    root = cfg.resolve(cfg.data.dataset_root)
    records = records_for_split(read_manifest(cfg.resolve(cfg.data.manifest)), args.split)
    if not records:
        print(f"no samples in split {args.split}", file=sys.stderr)
        return 2
    index = {c: i for i, c in enumerate(classes)}
    y_true, probs, failures = [], [], []
    for r in records:
        res = predictor.predict(root / r.rel_path)
        if res.status != "ok":
            failures.append({"rel_path": r.rel_path, "error": res.error})
            continue
        by_name = {p.class_name: p.score for p in res.predictions}
        probs.append([by_name[c] for c in classes])
        y_true.append(index[cfg.labels.folder_to_class[r.folder_label]])

    probs_arr = np.array(probs)
    pos_name = meta.get("positive_class")
    pos = classes.index(pos_name) if pos_name in classes else 1
    report = classification_report(np.array(y_true), probs_arr, classes,
                                   threshold=meta.get("decision_threshold"), positive_class=pos)
    report.update({
        "split": args.split,
        "checkpoint": ckpt.name,
        "model_version": meta["model_version"],
        "label_status": meta["label_status"],
        "threshold_selection": meta.get("threshold_selection"),
        "inference_failures": failures,
        "device": predictor.device_desc,
    })
    out = ckpt.parent / f"eval_{args.split}.json"
    out.write_text(json.dumps(report, indent=2))

    # Error analysis: sample each outcome for visual review.
    y = np.array(y_true)
    if len(classes) == 2 and meta.get("decision_threshold") is not None:
        pred = (probs_arr[:, pos] >= meta["decision_threshold"]).astype(int)
        pred = pred if pos == 1 else 1 - pred
    else:
        pred = probs_arr.argmax(axis=1)
    kept = [r for r in records if not any(f["rel_path"] == r.rel_path for f in failures)]
    outcomes = {"TP": (y == pos) & (pred == pos), "TN": (y != pos) & (pred != pos),
                "FP": (y != pos) & (pred == pos), "FN": (y == pos) & (pred != pos)}
    rng = np.random.default_rng(0)
    for name, mask in outcomes.items():
        idx = np.flatnonzero(mask)
        if idx.size == 0:
            continue
        chosen = sorted(rng.choice(idx, size=min(args.examples, idx.size), replace=False).tolist())
        make_contact_sheet(root, [kept[i] for i in chosen], ckpt.parent / f"eval_{args.split}_{name}.jpg",
                           title=f"{args.split} {name}: {idx.size} total, {len(chosen)} shown")

    printable = {k: report[k] for k in ("split", "n_samples", "confusion_matrix", "accuracy", "balanced_accuracy",
                                        "macro_f1", "average_precision", "roc_auc", "decision")}
    printable["per_class"] = report["per_class"]
    print(json.dumps(printable, indent=2))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
