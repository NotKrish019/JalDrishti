"""Reproducible object-detection training (torchvision Faster R-CNN, MobileNetV3-Large FPN).

Supervision: YOLO-format boxes (normalised `class xc yc w h`), one file per image, next to
the images as <split>/labels/<stem>.txt. An image with no label file is a background
(negative) image only where the config says so (`negatives_without_label_file`).

Selection discipline matches the classifier: best epoch by validation mAP@0.5, score
threshold chosen on validation, test split untouched (scripts/vision/evaluate_detector.py).
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import yaml
from PIL import Image

from vision.data.manifest import ImageRecord, read_manifest
from vision.inference.detector import DETECTOR_FORMAT, DETECTOR_PREPROCESSING
from vision.data.yolo_labels import parse_label_file
from vision.metrics.detection import evaluate_detections, image_level_scores
from vision.metrics.classification import average_precision, roc_auc, select_threshold
from vision.preprocessing.transforms import load_image
from vision.training.classifier import file_sha256, library_versions, seed_everything
from vision.training.config import REPO_ROOT, ConfigError

SUPPORTED_DETECTORS = ("fasterrcnn_mobilenet_v3_large_fpn",)


@dataclass
class DetectionConfig:
    name: str
    task: str
    classes: List[str]
    dataset_root: str
    manifest: str
    label_semantics: str = ""
    labels_verified: bool = False
    # folders (first path component) whose images may lack a label file and are then negatives
    negatives_without_label_file: List[str] = field(default_factory=list)
    arch: str = "fasterrcnn_mobilenet_v3_large_fpn"
    pretrained: bool = True
    weights_source: str = ""
    image_size: int = 512
    batch_size: int = 8
    epochs: int = 8
    learning_rate: float = 0.01
    momentum: float = 0.9
    weight_decay: float = 1e-4
    warmup_iters: int = 200
    seed: int = 42
    device: str = "cpu"
    num_threads: int = 0  # 0 = torch default
    max_train_batches: Optional[int] = None
    max_val_images: Optional[int] = None
    early_stopping_patience: int = 3
    hflip: bool = True
    color_jitter: float = 0.2
    output_dir: str = "vision/outputs/experiments"

    def resolve(self, p: str) -> Path:
        path = Path(p)
        return path if path.is_absolute() else REPO_ROOT / path

    def validate(self, allow_unverified_labels: bool = False) -> None:
        if self.task != "object_detection":
            raise ConfigError("detection config must have task: object_detection")
        if not self.classes or len(set(self.classes)) != len(self.classes):
            raise ConfigError("classes must be a non-empty list of distinct names")
        if self.arch not in SUPPORTED_DETECTORS:
            raise ConfigError(f"arch must be one of {SUPPORTED_DETECTORS}")
        if not allow_unverified_labels and not (self.labels_verified and self.label_semantics.strip()):
            raise ConfigError("labels_verified is false or label_semantics is empty")
        if not 128 <= self.image_size <= 1333 or self.batch_size < 1 or self.epochs < 1 or self.learning_rate <= 0:
            raise ConfigError("image_size/batch_size/epochs/learning_rate out of range")


def load_detection_config(path: Path | str) -> DetectionConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    try:
        return DetectionConfig(**raw)
    except TypeError as exc:
        raise ConfigError(f"invalid detection config {path}: {exc}") from exc


def label_path_for(rel_image: str) -> str:
    """'train/images/x.jpg' -> 'train/labels/x.txt' (YOLO convention)."""
    p = Path(rel_image)
    parts = list(p.parts)
    if "images" in parts:
        parts[len(parts) - 1 - parts[::-1].index("images")] = "labels"
    return Path(*parts).with_suffix(".txt").as_posix()


def load_targets(root: Path, rec: ImageRecord, n_classes: int, negatives_ok: Sequence[str]) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    """Return (boxes xyxy in original pixels, labels) or None when the image has no usable label."""
    lab = root / label_path_for(rec.rel_path)
    if not lab.is_file():
        if rec.rel_path.split("/")[0] in negatives_ok:
            return np.zeros((0, 4), np.float32), np.zeros((0,), np.int64)
        return None
    boxes, problems = parse_label_file(lab, n_classes)
    if problems:
        return None
    w, h = rec.width or 0, rec.height or 0
    xyxy = np.array([[(b.xc - b.w / 2) * w, (b.yc - b.h / 2) * h, (b.xc + b.w / 2) * w, (b.yc + b.h / 2) * h]
                     for b in boxes], np.float32).reshape(-1, 4)
    xyxy[:, [0, 2]] = xyxy[:, [0, 2]].clip(0, w)
    xyxy[:, [1, 3]] = xyxy[:, [1, 3]].clip(0, h)
    keep = (xyxy[:, 2] - xyxy[:, 0] >= 1) & (xyxy[:, 3] - xyxy[:, 1] >= 1)
    return xyxy[keep], np.array([b.class_id for b in boxes], np.int64)[keep]


class DetectionDataset:
    def __init__(self, root: Path, records: Sequence[ImageRecord], cfg: DetectionConfig, train: bool) -> None:
        self.root = root
        self.items = []
        for r in records:
            t = load_targets(root, r, len(cfg.classes), cfg.negatives_without_label_file)
            if t is not None:
                self.items.append((r, *t))
        self.train = train
        self.hflip = cfg.hflip and train
        self.jitter = cfg.color_jitter if train else 0.0

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, i: int):
        import torch
        from torchvision.transforms import v2
        from torchvision.transforms.functional import pil_to_tensor

        rec, boxes, labels = self.items[i]
        img = load_image(self.root / rec.rel_path)
        boxes = boxes.copy()
        if self.jitter:
            img = v2.ColorJitter(self.jitter, self.jitter, self.jitter * 0.75, 0.02)(img)
        x = pil_to_tensor(img).float() / 255.0
        if self.hflip and random.random() < 0.5:
            x = x.flip(-1)
            w = x.shape[-1]
            boxes[:, [0, 2]] = w - boxes[:, [2, 0]]
        # torchvision detection labels: 0 is background, so class k -> k + 1
        target = {"boxes": torch.from_numpy(boxes), "labels": torch.from_numpy(labels + 1)}
        return x, target, i


def collate(batch):
    return tuple(zip(*batch))


def build_detector(arch: str, n_classes: int, pretrained: bool, image_size: int):
    from torchvision.models.detection import FasterRCNN_MobileNet_V3_Large_FPN_Weights, fasterrcnn_mobilenet_v3_large_fpn
    from torchvision.models.detection.faster_rcnn import FastRCNNPredictor

    if arch != "fasterrcnn_mobilenet_v3_large_fpn":
        raise ValueError(f"unsupported detector {arch!r}")
    weights = FasterRCNN_MobileNet_V3_Large_FPN_Weights.COCO_V1 if pretrained else None
    m = fasterrcnn_mobilenet_v3_large_fpn(weights=weights, weights_backbone=None,
                                          min_size=image_size, max_size=image_size)
    m.roi_heads.box_predictor = FastRCNNPredictor(m.roi_heads.box_predictor.cls_score.in_features, n_classes + 1)
    return m, (str(weights) if weights else "random_init")


def predict_dataset(model, ds: DetectionDataset, device, batch_size: int = 8, limit: Optional[int] = None) -> List[Dict]:
    """Run the model over a dataset and return evaluate_detections-style records (0-based labels)."""
    import torch
    from torch.utils.data import DataLoader

    model.eval()
    out: List[Dict] = []
    n = 0
    loader = DataLoader(ds, batch_size=batch_size, shuffle=False, collate_fn=collate, num_workers=0)
    with torch.inference_mode():
        for xs, ts, idx in loader:
            preds = model([x.to(device) for x in xs])
            for p, t, i in zip(preds, ts, idx):
                out.append({
                    "rel_path": ds.items[i][0].rel_path,
                    "gt": {"boxes": t["boxes"].numpy(), "labels": t["labels"].numpy() - 1},
                    "pred": {"boxes": p["boxes"].cpu().numpy(), "labels": p["labels"].cpu().numpy() - 1,
                             "scores": p["scores"].cpu().numpy()},
                })
            n += len(xs)
            if limit is not None and n >= limit:
                break
    return out


def choose_score_threshold(records: List[Dict], class_names: Sequence[str]) -> Dict:
    """Score threshold maximising box-level F1 at IoU 0.5 on validation (coarse grid)."""
    best = None
    for th in np.round(np.arange(0.05, 0.96, 0.05), 2):
        op = evaluate_detections(records, class_names, iou_thresholds=(0.5,), score_threshold=float(th))["per_class"][0]["operating_point"]
        p, r = op["precision"] or 0.0, op["recall"] or 0.0
        f1 = 0.0 if p + r == 0 else 2 * p * r / (p + r)
        if best is None or f1 > best["f1"]:
            best = {"threshold": float(th), "precision": p, "recall": r, "f1": f1, "criterion": "max box F1 @ IoU 0.5"}
    return best  # type: ignore[return-value]


def full_report(records: List[Dict], class_names: Sequence[str], score_threshold: float,
                image_threshold: Optional[float] = None) -> Dict:
    rep = evaluate_detections(records, class_names, score_threshold=score_threshold)
    il = image_level_scores(records)
    y, s = il["y_true"], il["score"]
    image = {"n_images": int(len(y)), "with_ground_truth_boxes": int(y.sum()),
             "average_precision": average_precision(y, s) if y.sum() else None,
             "roc_auc": roc_auc(y, s)}
    th = image_threshold if image_threshold is not None else score_threshold
    pred = (s >= th).astype(int)
    tp, fp = int(((pred == 1) & (y == 1)).sum()), int(((pred == 1) & (y == 0)).sum())
    fn, tn = int(((pred == 0) & (y == 1)).sum()), int(((pred == 0) & (y == 0)).sum())
    image.update({
        "threshold": th,
        "confusion_matrix": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "specificity": tn / (tn + fp) if tn + fp else None,
    })
    rep["image_level"] = image
    return rep


def train_detector(cfg: DetectionConfig, allow_unverified_labels: bool = False, run_name: Optional[str] = None) -> Path:
    import torch
    from torch.utils.data import DataLoader

    cfg.validate(allow_unverified_labels)
    seed_everything(cfg.seed)
    if cfg.num_threads:
        torch.set_num_threads(cfg.num_threads)
    device = torch.device(cfg.device)

    root = cfg.resolve(cfg.dataset_root)
    manifest = cfg.resolve(cfg.manifest)
    records = read_manifest(manifest)
    train_ds = DetectionDataset(root, [r for r in records if r.split == "train"], cfg, train=True)
    val_ds = DetectionDataset(root, [r for r in records if r.split == "val"], cfg, train=False)
    if not len(train_ds) or not len(val_ds):
        raise RuntimeError("no train/val samples; run scripts/vision/make_detection_splits.py first")

    model, weights_id = build_detector(cfg.arch, len(cfg.classes), cfg.pretrained, cfg.image_size)
    model.to(device)
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.SGD(params, lr=cfg.learning_rate, momentum=cfg.momentum, weight_decay=cfg.weight_decay)
    g = torch.Generator().manual_seed(cfg.seed)
    loader = DataLoader(train_ds, batch_size=cfg.batch_size, shuffle=True, collate_fn=collate, num_workers=0, generator=g)
    steps_per_epoch = min(len(loader), cfg.max_train_batches or len(loader))
    total = steps_per_epoch * cfg.epochs

    def lr_at(step: int) -> float:
        if step < cfg.warmup_iters:
            return cfg.learning_rate * (0.001 + 0.999 * step / cfg.warmup_iters)
        prog = (step - cfg.warmup_iters) / max(1, total - cfg.warmup_iters)
        return cfg.learning_rate * 0.5 * (1 + np.cos(np.pi * prog))

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = run_name or f"{stamp}-{cfg.arch}"
    run_dir = cfg.resolve(cfg.output_dir) / cfg.name / run_id
    if run_dir.exists():
        raise FileExistsError(f"run directory already exists, refusing to overwrite: {run_dir}")
    run_dir.mkdir(parents=True)
    label_status = "verified" if cfg.labels_verified and not allow_unverified_labels else "unverified"
    n_pos = sum(1 for it in train_ds.items if len(it[1]))
    meta = {
        "run_id": run_id, "status": "running", "started_utc": stamp, "label_status": label_status,
        "config": asdict(cfg), "device": str(device), "torch_threads": torch.get_num_threads(),
        "initial_weights": weights_id, "versions": library_versions(), "manifest_sha256": file_sha256(manifest),
        "train_images": len(train_ds), "train_images_with_boxes": n_pos,
        "train_boxes": int(sum(len(it[1]) for it in train_ds.items)), "val_images": len(val_ds),
    }
    (run_dir / "run.json").write_text(json.dumps(meta, indent=2))

    history, best, best_epoch, stale, step = [], -1.0, 0, 0, 0
    start = time.perf_counter()
    try:
        for epoch in range(1, cfg.epochs + 1):
            model.train()
            t0, losses, seen = time.perf_counter(), [], 0
            for b, (xs, ts, _) in enumerate(loader):
                if cfg.max_train_batches is not None and b >= cfg.max_train_batches:
                    break
                for pg in opt.param_groups:
                    pg["lr"] = lr_at(step)
                loss_dict = model([x.to(device) for x in xs], [{k: v.to(device) for k, v in t.items()} for t in ts])
                loss = sum(loss_dict.values())
                if not torch.isfinite(loss):
                    raise FloatingPointError(f"non-finite loss at epoch {epoch} batch {b}: {loss_dict}")
                opt.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(params, 10.0)
                opt.step()
                losses.append(loss.item())
                seen += len(xs)
                step += 1
                if b % 50 == 0:
                    print(f"epoch {epoch} batch {b}/{steps_per_epoch} loss {loss.item():.3f} "
                          f"lr {lr_at(step):.4f} {time.perf_counter() - t0:.0f}s", flush=True)
            train_seconds = time.perf_counter() - t0
            preds = predict_dataset(model, val_ds, device, limit=cfg.max_val_images)
            rep = evaluate_detections(preds, cfg.classes, score_threshold=0.5)
            row = {"epoch": epoch, "train_loss": float(np.mean(losses)), "train_images": seen,
                   "val_map50": rep["map50"], "val_map50_95": rep["map50_95"],
                   "train_seconds": train_seconds, "val_seconds": time.perf_counter() - t0 - train_seconds}
            history.append(row)
            (run_dir / "history.json").write_text(json.dumps(history, indent=2))
            print(json.dumps(row), flush=True)
            score = rep["map50"] or 0.0
            if score > best:
                best, best_epoch, stale = score, epoch, 0
                torch.save(model.state_dict(), run_dir / "best_weights.pt")
            else:
                stale += 1
                if stale >= cfg.early_stopping_patience:
                    print(f"early stopping at epoch {epoch}", flush=True)
                    break
        torch.save(model.state_dict(), run_dir / "last_weights.pt")
    except BaseException as exc:
        meta.update(status="failed", error=f"{type(exc).__name__}: {exc}", history=history)
        (run_dir / "run.json").write_text(json.dumps(meta, indent=2))
        raise

    model.load_state_dict(torch.load(run_dir / "best_weights.pt", map_location=device, weights_only=True))
    preds = predict_dataset(model, val_ds, device)
    th = choose_score_threshold(preds, cfg.classes)
    il = image_level_scores(preds)
    image_th = select_threshold(il["y_true"], il["score"], "f1") if 0 < il["y_true"].sum() < len(il["y_true"]) else None
    val_report = full_report(preds, cfg.classes, th["threshold"], image_th["threshold"] if image_th else None)
    val_report.update(score_threshold_selection=th, image_threshold_selection=image_th, split="val")
    (run_dir / "val_report.json").write_text(json.dumps(val_report, indent=2, default=float))

    torch.save({
        "format": DETECTOR_FORMAT,
        "state_dict": {k: v.detach().cpu() for k, v in model.state_dict().items()},
        "meta": {
            "model_name": f"jaldrishti-{cfg.name}", "model_version": run_id, "task_type": "object_detection",
            "arch": cfg.arch, "classes": list(cfg.classes), "image_size": cfg.image_size,
            "score_threshold": th["threshold"], "score_threshold_selection": th,
            "image_threshold": image_th["threshold"] if image_th else th["threshold"],
            "preprocessing_version": DETECTOR_PREPROCESSING, "label_status": label_status,
            "label_semantics": cfg.label_semantics, "best_epoch": best_epoch,
            "selection_metric": "val_map50", "trained_utc": stamp,
        },
    }, run_dir / "model.pt")
    meta.update(status="completed", best_epoch=best_epoch, best_val_map50=best, epochs_run=len(history),
                training_seconds=time.perf_counter() - start, score_threshold=th, image_threshold=image_th,
                artefacts=["model.pt", "best_weights.pt", "last_weights.pt", "history.json", "val_report.json"])
    (run_dir / "run.json").write_text(json.dumps(meta, indent=2, default=float))
    return run_dir
