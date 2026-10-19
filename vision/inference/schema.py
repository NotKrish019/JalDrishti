"""The vision inference output contract (image classification).

The JSON Schema lives in vision/configs/inference_output.schema.json and is what the backend
should validate against. Fields that would imply capabilities this model does not have
(bounding boxes, masks, severity, safety) are deliberately absent.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

OUTPUT_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "configs" / "inference_output.schema.json"
SCHEMA_VERSION = "1.0"
# Shared by the trainer (writer) and the predictor (reader).
CHECKPOINT_FORMAT = "jaldrishti-vision-classifier/1"

DISCLAIMER = (
    "Image-level model output for human review. It indicates whether the image resembles the "
    "training examples of each class; it does not locate defects, assess structural safety, "
    "identify materials, or recommend a repair."
)


@dataclass
class ClassScore:
    class_id: int
    class_name: str
    score: float  # softmax output; uncalibrated unless model metadata says otherwise


@dataclass
class InferenceResult:
    status: str  # "ok" | "error"
    task_type: str = "image_classification"
    schema_version: str = SCHEMA_VERSION
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    label_status: Optional[str] = None  # "verified" | "unverified"
    preprocessing_version: Optional[str] = None
    image: Optional[Dict[str, int]] = None  # {"width": ..., "height": ...} of the decoded input
    predictions: List[ClassScore] = field(default_factory=list)  # sorted by score, descending
    top_class: Optional[str] = None
    decision: Optional[Dict[str, Any]] = None  # threshold rule, when the model defines one
    warnings: List[str] = field(default_factory=list)
    error: Optional[Dict[str, str]] = None  # {"code": ..., "message": ...} when status == "error"
    timing_ms: Optional[Dict[str, float]] = None
    disclaimer: str = DISCLAIMER

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


def validate_result(payload: Dict[str, Any]) -> None:
    """Raise jsonschema.ValidationError if payload does not match the published contract."""
    import jsonschema

    schema = json.loads(OUTPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(payload, schema)
