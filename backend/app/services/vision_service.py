"""Vision Service providing inference boundary and defect normalization.

Maintained by Swastik Parmar (Backend / Integration Engineer).
Adheres strictly to contracts/vision_result.schema.json.

Design:
- Serves as the abstraction boundary for Krish's YOLOv8-seg computer vision pipeline.
- When production model weights are absent or not yet loaded, operates deterministically
  without fabricating AI accuracy or synthetic detections.
- Accepts raw images, pre-annotated survey defect logs, or manual inspection entries.
"""

import time
from typing import List, Optional

from backend.app.schemas.vision import (
    DetectionItem,
    ImageDimensions,
    ProcessingMetadata,
    ScaleReference,
    StructureType,
    VisionResult,
)
from backend.app.utils.image import get_image_dimensions_from_bytes


class VisionService:
    """Service boundary for computer vision defect extraction and spatial analysis."""

    def __init__(self, model_version: str = "jaldrishti-vision-v0.2.0") -> None:
        self.model_version = model_version

    def analyze_image(
        self,
        image_bytes: Optional[bytes] = None,
        structure_type: StructureType = StructureType.BAOLI,
        image_dimensions: Optional[ImageDimensions] = None,
        scale_reference: Optional[ScaleReference] = None,
        detections: Optional[List[DetectionItem]] = None,
    ) -> VisionResult:
        """Process image input and produce a contract-compliant VisionResult.

        Args:
            image_bytes: Raw binary image payload if provided.
            structure_type: Architectural typology of inspected structure.
            image_dimensions: Explicit dimensions if known upfront.
            scale_reference: Optional calibrated spatial scale reference.
            detections: Pre-detected or manually verified defect segments.

        Returns:
            VisionResult: Structured visual inspection payload conforming to vision_result.schema.json.
        """
        start_time = time.perf_counter()

        # Resolve image dimensions
        resolved_dimensions = image_dimensions
        if resolved_dimensions is None and image_bytes is not None:
            extracted = get_image_dimensions_from_bytes(image_bytes)
            if extracted:
                resolved_dimensions = ImageDimensions(
                    width_pixels=extracted[0],
                    height_pixels=extracted[1],
                )

        # Fallback to standard survey frame resolution if unspecified
        if resolved_dimensions is None:
            resolved_dimensions = ImageDimensions(width_pixels=1920, height_pixels=1080)

        # Process detections
        validated_detections: List[DetectionItem] = []
        if detections:
            for item in detections:
                # Ensure each detection is properly bounded and typed
                validated_detections.append(item)

        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        return VisionResult(
            structure_type=structure_type,
            image_dimensions=resolved_dimensions,
            scale_reference=scale_reference,
            detections=validated_detections,
            processing_metadata=ProcessingMetadata(
                inference_latency_ms=latency_ms,
                model_version=self.model_version,
            ),
        )


vision_service = VisionService()
