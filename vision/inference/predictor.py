"""Image-classification predictor.

Usage (backend side):

    predictor = ImageClassifierPredictor.from_checkpoint("path/to/model.pt", device="auto")
    result = predictor.predict(image_bytes)        # path, bytes, PIL image or HxWx3 uint8 array
    payload = result.to_dict()                     # matches configs/inference_output.schema.json

Load the predictor once and reuse it. `predict` never raises for bad *input*: unreadable,
empty, oversized or unsupported images come back as `status="error"` with a stable code.
Loading a missing or malformed checkpoint raises `ModelLoadError`.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

from vision.inference.schema import CHECKPOINT_FORMAT, ClassScore, InferenceResult
from vision.preprocessing.transforms import (
    PREPROCESSING_VERSION,
    ImageLimits,
    ImageSource,
    ImageValidationError,
    load_image,
    to_model_tensor,
)

_REQUIRED_META = ("model_name", "model_version", "arch", "classes", "image_size", "preprocessing_version", "label_status")


class ModelLoadError(RuntimeError):
    pass


class ImageClassifierPredictor:
    def __init__(self, model, meta: Dict[str, Any], device, device_desc: str, limits: ImageLimits = ImageLimits()) -> None:
        self.model = model
        self.meta = meta
        self.device = device
        self.device_desc = device_desc
        self.limits = limits
        self._lock = threading.Lock()  # one forward pass at a time: bounded memory under concurrency

    @classmethod
    def from_checkpoint(cls, path: Path | str, device: str = "auto", limits: ImageLimits = ImageLimits()) -> "ImageClassifierPredictor":
        import torch

        from vision.training.backbones import build_classifier, select_device

        path = Path(path)
        if not path.is_file():
            raise ModelLoadError(f"checkpoint not found: {path.name}")
        try:
            ckpt = torch.load(path, map_location="cpu", weights_only=True)
        except Exception as exc:  # malformed or unsafe pickle content
            raise ModelLoadError(f"could not read checkpoint {path.name}: {type(exc).__name__}") from exc
        if not isinstance(ckpt, dict) or ckpt.get("format") != CHECKPOINT_FORMAT:
            raise ModelLoadError(f"{path.name} is not a {CHECKPOINT_FORMAT} checkpoint")
        meta = ckpt.get("meta") or {}
        missing = [k for k in _REQUIRED_META if k not in meta]
        if missing:
            raise ModelLoadError(f"checkpoint metadata missing: {missing}")
        classes = meta["classes"]
        if not isinstance(classes, list) or len(classes) < 2 or len(set(classes)) != len(classes):
            raise ModelLoadError("checkpoint class mapping is invalid")
        if meta["preprocessing_version"] != PREPROCESSING_VERSION:
            raise ModelLoadError(
                f"checkpoint expects preprocessing {meta['preprocessing_version']!r}, "
                f"this code provides {PREPROCESSING_VERSION!r}"
            )
        model, _ = build_classifier(meta["arch"], len(classes), pretrained=False)
        try:
            model.load_state_dict(ckpt["state_dict"])
        except Exception as exc:
            raise ModelLoadError(f"weights do not match architecture {meta['arch']}: {exc}") from exc
        dev, desc = select_device(device)
        model.to(dev).eval()
        return cls(model, meta, dev, desc, limits)

    def _error(self, code: str, message: str, warnings=None) -> InferenceResult:
        return InferenceResult(
            status="error",
            model_name=self.meta["model_name"],
            model_version=self.meta["model_version"],
            label_status=self.meta["label_status"],
            preprocessing_version=PREPROCESSING_VERSION,
            warnings=list(warnings or []),
            error={"code": code, "message": message},
        )

    def predict(self, source: ImageSource) -> InferenceResult:
        import torch

        warnings = []
        if self.meta["label_status"] != "verified":
            warnings.append(
                "This model was trained on unverified folder labels and is a pipeline test only. "
                "Its outputs must not be shown as findings."
            )
        t0 = time.perf_counter()
        try:
            img = load_image(source, self.limits)
        except ImageValidationError as exc:
            return self._error(exc.code, str(exc), warnings)
        width, height = img.size
        x = to_model_tensor(img, int(self.meta["image_size"])).unsqueeze(0)
        t1 = time.perf_counter()
        try:
            with self._lock, torch.inference_mode():
                logits = self.model(x.to(self.device))
                probs = torch.softmax(logits.float(), dim=1)[0].cpu().tolist()
        except Exception as exc:
            return self._error("inference_failed", f"{type(exc).__name__} during forward pass", warnings)
        t2 = time.perf_counter()

        classes = self.meta["classes"]
        scores = sorted(
            (ClassScore(class_id=i, class_name=c, score=float(p)) for i, (c, p) in enumerate(zip(classes, probs))),
            key=lambda s: (-s.score, s.class_id),
        )
        decision = None
        th, pos = self.meta.get("decision_threshold"), self.meta.get("positive_class")
        if th is not None and pos in classes:
            decision = {
                "rule": "score_threshold",
                "positive_class": pos,
                "threshold": float(th),
                "positive": probs[classes.index(pos)] >= float(th),
            }
        t3 = time.perf_counter()
        return InferenceResult(
            status="ok",
            model_name=self.meta["model_name"],
            model_version=self.meta["model_version"],
            label_status=self.meta["label_status"],
            preprocessing_version=PREPROCESSING_VERSION,
            image={"width": width, "height": height},
            predictions=scores,
            top_class=scores[0].class_name,
            decision=decision,
            warnings=warnings,
            timing_ms={
                "preprocess": (t1 - t0) * 1000,
                "forward": (t2 - t1) * 1000,
                "postprocess": (t3 - t2) * 1000,
                "total": (t3 - t0) * 1000,
            },
        )
