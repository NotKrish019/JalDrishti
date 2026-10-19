"""Reproducible image-classification training.

Selection discipline:
* the best epoch is chosen on the validation split (`train.selection_metric`);
* the binary decision threshold is chosen on the validation split, after training;
* the test split is never touched here. `scripts/vision/evaluate_classifier.py --split test`
  evaluates a finished checkpoint once the model and threshold are fixed.
"""

from __future__ import annotations

import hashlib
import json
import platform
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from vision.data.manifest import ImageRecord, read_manifest
from vision.inference.schema import CHECKPOINT_FORMAT
from vision.metrics.classification import classification_report, select_threshold
from vision.preprocessing.transforms import PREPROCESSING_VERSION, build_train_transform, load_image, to_model_tensor
from vision.training.backbones import build_classifier, select_device
from vision.training.config import ExperimentConfig



def seed_everything(seed: int) -> None:
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True


class ManifestDataset:
    """Images listed in a manifest for one split, with labels from the folder mapping."""

    def __init__(
        self,
        root: Path,
        records: Sequence[ImageRecord],
        folder_to_class: Dict[str, str],
        classes: Sequence[str],
        transform: Callable,
    ) -> None:
        self.root = root
        self.records = list(records)
        index = {c: i for i, c in enumerate(classes)}
        self.labels = [index[folder_to_class[r.folder_label]] for r in self.records]  # type: ignore[index]
        self.transform = transform

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, i: int):
        img = load_image(self.root / self.records[i].rel_path)
        return self.transform(img), self.labels[i]


def records_for_split(records: Sequence[ImageRecord], split: str) -> List[ImageRecord]:
    return [r for r in records if r.split == split and r.exclusion_reason is None]


def library_versions() -> Dict[str, str]:
    import PIL
    import torch
    import torchvision

    return {
        "python": platform.python_version(),
        "torch": torch.__version__,
        "torchvision": torchvision.__version__,
        "numpy": np.__version__,
        "pillow": PIL.__version__,
        "platform": platform.platform(),
    }


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 16):
            h.update(chunk)
    return h.hexdigest()


def predict_probabilities(model, loader, device, max_batches: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray, float]:
    """Return (probabilities N x C, labels N, mean cross-entropy loss)."""
    import torch
    import torch.nn.functional as F

    model.eval()
    probs, labels, losses = [], [], []
    with torch.inference_mode():
        for b, (x, y) in enumerate(loader):
            if max_batches is not None and b >= max_batches:
                break
            x, y = x.to(device), y.to(device)
            logits = model(x)
            losses.append(float(F.cross_entropy(logits, y, reduction="sum")))
            probs.append(torch.softmax(logits.float(), dim=1).cpu().numpy())
            labels.append(y.cpu().numpy())
    n = sum(len(l) for l in labels)
    return np.concatenate(probs), np.concatenate(labels), (sum(losses) / max(1, n))


def _selection_value(metric: str, report: Dict, loss: float) -> float:
    if metric == "val_loss":
        return -loss
    key = {"val_average_precision": "average_precision", "val_macro_f1": "macro_f1",
           "val_balanced_accuracy": "balanced_accuracy"}[metric]
    v = report.get(key)
    return float("-inf") if v is None else float(v)


def train(cfg: ExperimentConfig, allow_unverified_labels: bool = False, run_name: Optional[str] = None) -> Path:
    """Train and return the run directory. Raises before doing any work if the config is invalid."""
    import torch
    from torch.utils.data import DataLoader

    cfg.validate(allow_unverified_labels=allow_unverified_labels)
    t = cfg.train
    seed_everything(t.seed)
    device, device_desc = select_device(t.device)

    root = cfg.resolve(cfg.data.dataset_root)
    manifest_path = cfg.resolve(cfg.data.manifest)
    records = read_manifest(manifest_path)
    train_recs = records_for_split(records, "train")
    val_recs = records_for_split(records, "val")
    if not train_recs or not val_recs:
        raise RuntimeError("manifest has no train/val assignments; run scripts/vision/make_splits.py first")

    classes = cfg.labels.classes
    train_ds = ManifestDataset(root, train_recs, cfg.labels.folder_to_class, classes,
                               build_train_transform(t.image_size, t.augmentation))
    val_ds = ManifestDataset(root, val_recs, cfg.labels.folder_to_class, classes,
                             lambda img: to_model_tensor(img, t.image_size))
    g = torch.Generator().manual_seed(t.seed)
    pin = device.type == "cuda"
    train_loader = DataLoader(train_ds, batch_size=t.batch_size, shuffle=True, num_workers=t.num_workers,
                              generator=g, pin_memory=pin, drop_last=False)
    val_loader = DataLoader(val_ds, batch_size=t.batch_size, shuffle=False, num_workers=t.num_workers, pin_memory=pin)

    counts = np.bincount(train_ds.labels, minlength=len(classes)).astype(np.float64)
    if (counts == 0).any():
        raise RuntimeError(f"a class has no training samples: {dict(zip(classes, counts.tolist()))}")
    weights = None
    if t.class_weighting == "inverse_frequency":
        w = counts.sum() / (len(classes) * counts)
        weights = torch.tensor(w, dtype=torch.float32, device=device)

    model, weights_id = build_classifier(cfg.model.arch, len(classes), cfg.model.pretrained)
    model.to(device)
    criterion = torch.nn.CrossEntropyLoss(weight=weights)
    optimiser = torch.optim.AdamW(model.parameters(), lr=t.learning_rate, weight_decay=t.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimiser, T_max=t.epochs)
    use_amp = t.mixed_precision and device.type == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = run_name or f"{stamp}-{cfg.model.arch}"
    run_dir = cfg.resolve(cfg.output_dir) / cfg.name / run_id
    if run_dir.exists():
        raise FileExistsError(f"run directory already exists, refusing to overwrite: {run_dir}")
    run_dir.mkdir(parents=True)
    label_status = "verified" if cfg.labels.verified and not allow_unverified_labels else "unverified"
    positive_index = classes.index(cfg.labels.positive_class) if cfg.labels.positive_class else (1 if len(classes) == 2 else None)

    run_meta = {
        "run_id": run_id,
        "status": "running",
        "started_utc": stamp,
        "label_status": label_status,
        "config": cfg.to_dict(),
        "device": device_desc,
        "initial_weights": weights_id,
        "versions": library_versions(),
        "manifest_sha256": file_sha256(manifest_path),
        "train_class_counts": dict(zip(classes, counts.astype(int).tolist())),
        "val_size": len(val_ds),
        "preprocessing_version": PREPROCESSING_VERSION,
    }
    (run_dir / "run.json").write_text(json.dumps(run_meta, indent=2))

    history: List[Dict] = []
    best_value, best_epoch, stale = float("-inf"), -1, 0
    start = time.perf_counter()
    try:
        for epoch in range(1, t.epochs + 1):
            model.train()
            ep_loss, ep_n, ep_start = 0.0, 0, time.perf_counter()
            for b, (x, y) in enumerate(train_loader):
                if t.max_train_batches is not None and b >= t.max_train_batches:
                    break
                x, y = x.to(device, non_blocking=pin), y.to(device, non_blocking=pin)
                optimiser.zero_grad(set_to_none=True)
                with torch.autocast(device_type="cuda", enabled=use_amp):
                    loss = criterion(model(x), y)
                scaler.scale(loss).backward()
                scaler.step(optimiser)
                scaler.update()
                ep_loss += loss.item() * len(y)
                ep_n += len(y)
            scheduler.step()

            probs, labels, val_loss = predict_probabilities(model, val_loader, device)
            report = classification_report(labels, probs, classes)
            value = _selection_value(t.selection_metric, report, val_loss)
            row = {
                "epoch": epoch,
                "train_loss": ep_loss / max(1, ep_n),
                "val_loss": val_loss,
                "val_accuracy": report["accuracy"],
                "val_balanced_accuracy": report["balanced_accuracy"],
                "val_macro_f1": report["macro_f1"],
                "val_average_precision": report.get("average_precision"),
                "seconds": time.perf_counter() - ep_start,
            }
            if device.type == "cuda":
                row["peak_gpu_mb"] = torch.cuda.max_memory_allocated(device) / 2**20
            history.append(row)
            (run_dir / "history.json").write_text(json.dumps(history, indent=2))
            print(json.dumps(row))
            if value > best_value:
                best_value, best_epoch, stale = value, epoch, 0
                torch.save(model.state_dict(), run_dir / "best_weights.pt")
            else:
                stale += 1
                if stale >= t.early_stopping_patience:
                    print(f"early stopping at epoch {epoch} (no improvement for {stale} epochs)")
                    break
        torch.save(model.state_dict(), run_dir / "last_weights.pt")
    except BaseException as exc:
        run_meta.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        (run_dir / "run.json").write_text(json.dumps(run_meta, indent=2))
        raise

    # Reload the best epoch and fix the binary threshold on validation data.
    model.load_state_dict(torch.load(run_dir / "best_weights.pt", map_location=device, weights_only=True))
    probs, labels, val_loss = predict_probabilities(model, val_loader, device)
    threshold = None
    if len(classes) == 2 and positive_index is not None:
        pos = (labels == positive_index).astype(np.int64)
        if pos.sum() > 0:
            threshold = select_threshold(pos, probs[:, positive_index], t.threshold_criterion, t.threshold_target)
    val_report = classification_report(labels, probs, classes,
                                       threshold=threshold["threshold"] if threshold else None,
                                       positive_class=positive_index or 1)
    (run_dir / "val_report.json").write_text(json.dumps(val_report, indent=2))

    checkpoint = {
        "format": CHECKPOINT_FORMAT,
        "state_dict": {k: v.detach().cpu() for k, v in model.state_dict().items()},
        "meta": {
            "model_name": f"jaldrishti-{cfg.name}",
            "model_version": run_id,
            "task_type": "image_classification",
            "arch": cfg.model.arch,
            "classes": list(classes),
            "positive_class": classes[positive_index] if positive_index is not None else None,
            "decision_threshold": threshold["threshold"] if threshold else None,
            "threshold_selection": threshold,
            "image_size": t.image_size,
            "preprocessing_version": PREPROCESSING_VERSION,
            "label_status": label_status,
            "label_semantics": cfg.labels.semantics,
            "best_epoch": best_epoch,
            "selection_metric": t.selection_metric,
            "trained_utc": stamp,
        },
    }
    torch.save(checkpoint, run_dir / "model.pt")
    run_meta.update(
        status="completed",
        best_epoch=best_epoch,
        selection_metric=t.selection_metric,
        best_selection_value=best_value,
        decision_threshold=threshold,
        training_seconds=time.perf_counter() - start,
        epochs_run=len(history),
        artefacts=["model.pt", "best_weights.pt", "last_weights.pt", "history.json", "val_report.json"],
    )
    (run_dir / "run.json").write_text(json.dumps(run_meta, indent=2))
    return run_dir
