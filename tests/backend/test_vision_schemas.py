"""Unit tests for VisionResult schema contract."""

import pytest
from pydantic import ValidationError

from backend.app.schemas.vision import (
    DetectionItem,
    ImageDimensions,
    ProcessingMetadata,
    RelativeSeverity,
    ScaleReference,
    StructureType,
    VisionDefectClass,
    VisionResult,
)


def test_valid_vision_result() -> None:
    """Verify valid VisionResult data model instantiation and serialization."""
    result = VisionResult(
        structure_type=StructureType.BAOLI,
        image_dimensions=ImageDimensions(width_pixels=1920, height_pixels=1080),
        scale_reference=ScaleReference(
            calibrated=True,
            pixels_per_millimeter=2.5,
            method="reference_step_depth",
        ),
        detections=[
            DetectionItem(
                class_name=VisionDefectClass.CRACK.value,
                confidence=0.92,
                bounding_box=[100.0, 150.0, 250.0, 300.0],
                segmentation_mask_reference="masks/crack_01.rle",
                pixel_area=450.5,
                coverage_ratio=0.015,
                component_count=1,
                total_length_pixels=120.5,
                largest_component_length_pixels=120.5,
                relative_severity=RelativeSeverity.MODERATE,
                burden_score=1.84,
            ),
            DetectionItem(
                class_name=VisionDefectClass.VEGETATION.value,
                confidence=0.88,
                bounding_box=[300.0, 400.0, 500.0, 600.0],
                pixel_area=1200.0,
                coverage_ratio=0.045,
                component_count=3,
                burden_score=2.64,
            ),
        ],
        processing_metadata=ProcessingMetadata(
            inference_latency_ms=145.2,
            model_version="baoli-yolo-v8-seg-0.1.0",
        ),
    )

    data = result.model_dump(mode="json")
    assert data["structure_type"] == "baoli"
    assert data["image_dimensions"]["width_pixels"] == 1920
    assert len(data["detections"]) == 2
    assert data["detections"][0]["burden_score"] == 1.84
    assert data["detections"][0]["class_name"] == "crack"


def test_vision_result_missing_required_fields_fails() -> None:
    """Verify validation failure when required fields are missing."""
    with pytest.raises(ValidationError):
        # Missing structure_type and image_dimensions
        VisionResult.model_validate({"detections": []})


def test_detection_invalid_confidence_fails() -> None:
    """Verify confidence out of [0.0, 1.0] range raises ValidationError."""
    with pytest.raises(ValidationError):
        DetectionItem(
            class_name="crack",
            confidence=1.5,  # Invalid: > 1.0
            bounding_box=[10.0, 20.0, 30.0, 40.0],
            pixel_area=100.0,
            coverage_ratio=0.01,
            component_count=1,
        )

    with pytest.raises(ValidationError):
        DetectionItem(
            class_name="crack",
            confidence=-0.1,  # Invalid: < 0.0
            bounding_box=[10.0, 20.0, 30.0, 40.0],
            pixel_area=100.0,
            coverage_ratio=0.01,
            component_count=1,
        )


def test_detection_invalid_bounding_box_length_fails() -> None:
    """Verify bounding box requires exactly 4 coordinates."""
    with pytest.raises(ValidationError):
        DetectionItem(
            class_name="spalling",
            confidence=0.85,
            bounding_box=[10.0, 20.0, 30.0],  # Invalid: only 3 items
            pixel_area=50.0,
            coverage_ratio=0.005,
            component_count=1,
        )


def test_image_dimensions_positive_integers_required() -> None:
    """Verify image dimensions must be >= 1."""
    with pytest.raises(ValidationError):
        ImageDimensions(width_pixels=0, height_pixels=100)

    with pytest.raises(ValidationError):
        ImageDimensions(width_pixels=100, height_pixels=-5)
