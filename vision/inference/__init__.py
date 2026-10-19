"""Inference interface for the backend: load once, predict many, structured results."""

from vision.inference.detector import (
    DetectionPredictor,
    DetectionResult,
    DetectorLoadError,
    validate_detection_result,
)
from vision.inference.predictor import ImageClassifierPredictor, ModelLoadError
from vision.inference.schema import (
    DISCLAIMER,
    OUTPUT_SCHEMA_PATH,
    ClassScore,
    InferenceResult,
    validate_result,
)

__all__ = [
    "DetectionPredictor",
    "DetectionResult",
    "DetectorLoadError",
    "validate_detection_result",
    "DISCLAIMER",
    "OUTPUT_SCHEMA_PATH",
    "ClassScore",
    "ImageClassifierPredictor",
    "InferenceResult",
    "ModelLoadError",
    "validate_result",
]
