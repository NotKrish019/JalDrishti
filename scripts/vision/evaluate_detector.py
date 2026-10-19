"""Evaluate a detector checkpoint on one split of the detection manifest.

    python3 scripts/vision/evaluate_detector.py --checkpoint <run_dir>/model.pt \
        --config vision/configs/detection_pilot.yaml --split val
    # once the model and thresholds are final, exactly once:
    python3 scripts/vision/evaluate_detector.py ... --split test

Uses the box score threshold stored in the checkpoint (selected on validation) for boxes and for
the image-level flag (an image is flagged when at least one box passes it).
Writes <run_dir>/eval_<split>.json and review sheets eval_<split>_{misses,false_alarms,hits}.jpg
with ground truth in green and predictions (at the threshold) in red.
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

from PIL import Image, ImageDraw  # noqa: E402

from vision.data.manifest import read_manifest  # noqa: E402
from vision.inference.detector import DetectionPredictor  # noqa: E402
from vision.metrics.detection import box_iou  # noqa: E402
from vision.training.detection import DetectionDataset, full_report, load_detection_config, predict_dataset  # noqa: E402


def review_sheet(root: Path, items, out: Path, title: str, score_th: float, cols: int = 5, th: int = 220) -> None:
    rows = max(1, -(-len(items) // cols))
    sheet = Image.new("RGB", (cols * th, 32 + rows * (th + 22)), (24, 22, 20))
    d = ImageDraw.Draw(sheet)
    d.text((8, 10), title + "   green = annotated crack, red = model box", fill=(235, 225, 210))
    for i, r in enumerate(items):
        with Image.open(root / r["rel_path"]) as im:
            im = im.convert("RGB")
        dd = ImageDraw.Draw(im)
        for b in r["gt"]["boxes"]:
            dd.rectangle(list(map(float, b)), outline=(40, 220, 90), width=5)
        for b, s in zip(r["pred"]["boxes"], r["pred"]["scores"]):
            if s >= score_th:
                dd.rectangle(list(map(float, b)), outline=(240, 50, 40), width=4)
                dd.text((float(b[0]) + 4, float(b[1]) + 4), f"{s:.2f}", fill=(255, 230, 0))
        im = im.resize((th - 6, th - 6))
        x, y = (i % cols) * th, 32 + (i // cols) * (th + 22)
        sheet.paste(im, (x + 3, y + 3))
        d.text((x + 4, y + th + 3), r["rel_path"].split("/")[-1][:28], fill=(200, 190, 175))
    sheet.save(out, quality=88)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--split", choices=["val", "test"], default="val")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--examples", type=int, default=15)
    args = ap.parse_args()

    cfg = load_detection_config(args.config)
    ckpt = Path(args.checkpoint)
    predictor = DetectionPredictor.from_checkpoint(ckpt, device=args.device)
    meta = predictor.meta
    root = cfg.resolve(cfg.dataset_root)
    records = [r for r in read_manifest(cfg.resolve(cfg.manifest)) if r.split == args.split]
    ds = DetectionDataset(root, records, cfg, train=False)
    preds = predict_dataset(predictor.model, ds, predictor.device)
    # Image-level flag = any box at the score threshold, matching DetectionPredictor.
    report = full_report(preds, meta["classes"], float(meta["score_threshold"]), float(meta["score_threshold"]))
    report.update(split=args.split, checkpoint=ckpt.name, model_version=meta["model_version"],
                  label_status=meta["label_status"], score_threshold=meta["score_threshold"],
                  image_threshold=meta["score_threshold"])

    # Per-image outcome at the operating point, for error analysis.
    st = float(meta["score_threshold"])
    hits, misses, false_alarms = [], [], []
    for r in preds:
        kept = r["pred"]["scores"] >= st
        pb, gb = r["pred"]["boxes"][kept], r["gt"]["boxes"]
        if len(gb) and len(pb) and (box_iou(pb, gb).max(axis=0) >= 0.5).all():
            hits.append(r)
        elif len(gb) and (not len(pb) or (box_iou(pb, gb).max(axis=0) < 0.5).any()):
            misses.append(r)
        if (not len(gb) and len(pb)) or (len(gb) and len(pb) and (box_iou(pb, gb).max(axis=1) < 0.5).any()):
            false_alarms.append(r)
    report["error_analysis_counts"] = {"images_all_gt_matched": len(hits), "images_with_missed_gt": len(misses),
                                       "images_with_unmatched_predictions": len(false_alarms)}
    out = ckpt.parent / f"eval_{args.split}.json"
    out.write_text(json.dumps(report, indent=2, default=float))
    rng = np.random.default_rng(0)
    for name, group in (("hits", hits), ("misses", misses), ("false_alarms", false_alarms)):
        if group:
            pick = [group[i] for i in sorted(rng.choice(len(group), min(args.examples, len(group)), replace=False))]
            review_sheet(root, pick, ckpt.parent / f"eval_{args.split}_{name}.jpg",
                         f"{args.split} {name}: {len(group)} images, {len(pick)} shown", st)

    pc = report["per_class"][0]
    print(json.dumps({"split": args.split, "n_images": report["n_images"], "map50": report["map50"],
                      "map50_95": report["map50_95"], "ap75": pc["ap75"], "operating_point": pc["operating_point"],
                      "image_level": report["image_level"], "error_analysis": report["error_analysis_counts"]},
                     indent=2, default=float))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
