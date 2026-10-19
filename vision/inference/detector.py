"""Crack-detection predictor.

    predictor = DetectionPredictor.from_checkpoint("path/to/model.pt", device="cpu")
    result = predictor.predict(image_bytes)   # path, bytes, PIL image or HxWx3 uint8 RGB array
    payload = result.to_dict()                # matches configs/inference_output_detection.schema.json

Boxes are returned in the pixel coordinates of the decoded input (after EXIF orientation), as
[x_min, y_min, x_max, y_max]. Only boxes at or above the validation-selected score threshold
are returned in `detections`; the image-level summary uses the highest box score.
"""

from __future__ import annotations

import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from vision.preprocessing.transforms import ImageLimits, ImageSource, ImageValidationError, load_image

DETECTOR_FORMAT = "jaldrishti-vision-detector/1"
DETECTOR_PREPROCESSING = "rgb-01-torchvision-rcnn-resize-v1"
SCHEMA_VERSION = "1.0"
TRAINING_IMAGE_SIZE = (768, 768)
OUTPUT_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "configs" / "inference_output_detection.schema.json"
DETECTION_DISCLAIMER = (
    "Candidate crack regions for human review. A box marks where the image resembles annotated "
    "cracks in the training data; it does not measure crack width or depth, establish cause or "
    "activity, assess structural safety, or recommend a repair. The model was trained on brick "
    "masonry from a single site and has not been validated on other structures."
)
_REQUIRED = ("model_name", "model_version", "arch", "classes", "image_size", "score_threshold",
             "preprocessing_version", "label_status")


class DetectorLoadError(RuntimeError):
    pass


@dataclass
class Detection:
    class_id: int
    class_name: str
    confidence: float
    bbox: List[float]  # [x_min, y_min, x_max, y_max] in input pixels


@dataclass
class DetectionResult:
    status: str
    task_type: str = "object_detection"
    schema_version: str = SCHEMA_VERSION
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    label_status: Optional[str] = None
    preprocessing_version: Optional[str] = None
    image: Optional[Dict[str, int]] = None
    score_threshold: Optional[float] = None
    detections: List[Detection] = field(default_factory=list)
    image_level: Optional[Dict[str, Any]] = None
    warnings: List[str] = field(default_factory=list)
    error: Optional[Dict[str, str]] = None
    timing_ms: Optional[Dict[str, float]] = None
    disclaimer: str = DETECTION_DISCLAIMER

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def validate_detection_result(payload: Dict[str, Any]) -> None:
    """Raise jsonschema.ValidationError if payload does not match the published detection contract."""
    import json

    import jsonschema

    jsonschema.validate(payload, json.loads(OUTPUT_SCHEMA_PATH.read_text(encoding="utf-8")))


class DetectionPredictor:
    def __init__(self, model, meta: Dict[str, Any], device, limits: ImageLimits = ImageLimits()) -> None:
        self.model = model
        self.meta = meta
        self.device = device
        self.limits = limits
        self._lock = threading.Lock()

    @classmethod
    def from_checkpoint(cls, path: Path | str, device: str = "cpu", limits: ImageLimits = ImageLimits()) -> "DetectionPredictor":
        import torch

        from vision.training.backbones import select_device
        from vision.training.detection import build_detector

        path = Path(path)
        if not path.is_file():
            raise DetectorLoadError(f"checkpoint not found: {path.name}")
        try:
            ckpt = torch.load(path, map_location="cpu", weights_only=True)
        except Exception as exc:
            raise DetectorLoadError(f"could not read checkpoint {path.name}: {type(exc).__name__}") from exc
        if not isinstance(ckpt, dict) or ckpt.get("format") != DETECTOR_FORMAT:
            raise DetectorLoadError(f"{path.name} is not a {DETECTOR_FORMAT} checkpoint")
        meta = ckpt.get("meta") or {}
        missing = [k for k in _REQUIRED if k not in meta]
        if missing:
            raise DetectorLoadError(f"checkpoint metadata missing: {missing}")
        if not meta["classes"] or len(set(meta["classes"])) != len(meta["classes"]):
            raise DetectorLoadError("checkpoint class mapping is invalid")
        if meta["preprocessing_version"] != DETECTOR_PREPROCESSING:
            raise DetectorLoadError(f"checkpoint expects preprocessing {meta['preprocessing_version']!r}")
        model, _ = build_detector(meta["arch"], len(meta["classes"]), pretrained=False, image_size=int(meta["image_size"]))
        try:
            model.load_state_dict(ckpt["state_dict"])
        except Exception as exc:
            raise DetectorLoadError(f"weights do not match {meta['arch']}: {exc}") from exc
        dev, _ = select_device(device)
        model.to(dev).eval()
        return cls(model, meta, dev, limits)

    def _base(self, status: str, warnings: List[str]) -> DetectionResult:
        return DetectionResult(status=status, model_name=self.meta["model_name"], model_version=self.meta["model_version"],
                               label_status=self.meta["label_status"], preprocessing_version=DETECTOR_PREPROCESSING,
                               score_threshold=float(self.meta["score_threshold"]), warnings=warnings)

    def predict(self, source: ImageSource) -> DetectionResult:
        import torch
        from torchvision.transforms.functional import pil_to_tensor

        warnings: List[str] = []
        if self.meta["label_status"] != "verified":
            warnings.append("Trained on unverified labels: pipeline test only, not a finding.")
        t0 = time.perf_counter()
        try:
            img = load_image(source, self.limits)
        except ImageValidationError as exc:
            res = self._base("error", warnings)
            res.error = {"code": exc.code, "message": str(exc)}
            return res
        w, h = img.size
        x = pil_to_tensor(img).float().div_(255.0)
        t1 = time.perf_counter()
        try:
            with self._lock, torch.inference_mode():
                out = self.model([x.to(self.device)])[0]
        except Exception as exc:
            res = self._base("error", warnings)
            res.error = {"code": "inference_failed", "message": f"{type(exc).__name__} during forward pass"}
            return res
        t2 = time.perf_counter()
        th = float(self.meta["score_threshold"])
        classes = self.meta["classes"]
        boxes, scores, labels = out["boxes"].cpu().tolist(), out["scores"].cpu().tolist(), out["labels"].cpu().tolist()
        dets = []
        for b, s, l in zip(boxes, scores, labels):
            if s < th:
                continue
            x1, y1, x2, y2 = (max(0.0, min(float(v), float(lim))) for v, lim in zip(b, (w, h, w, h)))
            dets.append(Detection(class_id=int(l) - 1, class_name=classes[int(l) - 1], confidence=float(s),
                                  bbox=[round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)]))
        dets.sort(key=lambda d: -d.confidence)
        top = max(scores) if scores else 0.0
        # The image-level flag uses the box threshold, so it is true exactly when at least one box
        # is returned. A separately tuned image threshold (meta["image_threshold"]) was fitted on 29
        # easily separable background images and fired on out-of-domain photos with no boxes at all.
        image_th = th
        res = self._base("ok", warnings)
        res.image = {"width": w, "height": h}
        res.detections = dets
        res.image_level = {"max_score": float(top), "threshold": image_th, "candidate_present": top >= image_th}
        if (w, h) != TRAINING_IMAGE_SIZE:
            warnings.append("Input size differs from the 768x768 training images; results may be less reliable.")
        t3 = time.perf_counter()
        res.timing_ms = {"preprocess": (t1 - t0) * 1000, "forward": (t2 - t1) * 1000,
                         "postprocess": (t3 - t2) * 1000, "total": (t3 - t0) * 1000}
        return res
