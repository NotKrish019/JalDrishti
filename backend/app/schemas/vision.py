"""Computer Vision result schemas mirroring contracts/vision_result.schema.json.

Maintained by Swastik Parmar (Backend / Integration Engineer).
Captures relative/image-space measurements without premature physical scaling.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class StructureType(str, Enum):
    """Recognized traditional water structure architectural classifications."""

    BAOLI = "baoli"
    BAWARI = "bawari"
    KUND = "kund"
    VAV = "vav"
    TANK = "tank"
    UNKNOWN = "unknown"


class VisionDefectClass(str, Enum):
    """Initial and extended visual defect classes for BaoliGuard."""

    CRACK = "crack"
    SPALLING = "spalling"
    VEGETATION = "vegetation"
    VEGETATION_ROOT_INTRUSION = "vegetation_root_intrusion"
    EFFLORESCENCE = "efflorescence"
    BIOLOGICAL_GROWTH = "biological_growth"
    STONE_DISLODGEMENT = "stone_dislodgement"


class RelativeSeverity(str, Enum):
    """Relative visual defect severity based on coverage and morphology."""

    LOW = "low"
    MODERATE = "moderate"
    SEVERE = "severe"


class ImageDimensions(BaseModel):
    """Input image resolution in pixel coordinates."""

    model_config = ConfigDict(extra="ignore")

    width_pixels: int = Field(..., ge=1, description="Width of source image in pixels")
    height_pixels: int = Field(..., ge=1, description="Height of source image in pixels")


class ScaleReference(BaseModel):
    """Optional calibrated spatial scale when physical reference marker is present."""

    model_config = ConfigDict(extra="ignore")

    calibrated: Optional[bool] = Field(default=None, description="Whether spatial reference was calibrated")
    pixels_per_millimeter: Optional[float] = Field(
        default=None, ge=0.0, description="Calibrated scale in pixels per mm"
    )
    method: Optional[str] = Field(default=None, description="Method of calibration")


class DetectionItem(BaseModel):
    """Detected visual defect segment in image space."""

    model_config = ConfigDict(extra="ignore")

    class_name: str = Field(..., description="Defect classification label (e.g. crack, spalling, vegetation)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model detection confidence score")
    bounding_box: List[float] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Bounding coordinates [x_min, y_min, x_max, y_max] in pixels",
    )
    segmentation_mask_reference: Optional[str] = Field(
        default=None,
        description="Relative URI or mask file identifier referencing RLE / binary mask array",
    )
    pixel_area: float = Field(..., ge=0.0, description="Defect pixel area in image space")
    coverage_ratio: float = Field(
        ..., ge=0.0, le=1.0, description="Ratio of defect pixel area to total region area"
    )
    component_count: int = Field(
        ..., ge=1, description="Number of connected defect components in group"
    )
    total_length_pixels: Optional[float] = Field(
        default=None, ge=0.0, description="Estimated centerline skeleton length in pixels"
    )
    largest_component_length_pixels: Optional[float] = Field(
        default=None, ge=0.0, description="Pixel length of largest contiguous defect component"
    )
    relative_severity: RelativeSeverity = Field(
        default=RelativeSeverity.MODERATE, description="Relative visual defect severity"
    )
    burden_score: Optional[float] = Field(
        default=None, ge=0.0, description="Calculated visual defect burden score"
    )


class ProcessingMetadata(BaseModel):
    """Inference execution metadata."""

    model_config = ConfigDict(extra="ignore")

    inference_latency_ms: Optional[float] = Field(default=None, description="Inference latency in milliseconds")
    model_version: Optional[str] = Field(default=None, description="Vision model release tag")


class VisionResult(BaseModel):
    """Output contract for computer vision inference pipeline."""

    model_config = ConfigDict(extra="ignore")

    structure_type: StructureType = Field(..., description="Identified structure type")
    image_dimensions: ImageDimensions = Field(..., description="Dimensions of analyzed image")
    scale_reference: Optional[ScaleReference] = Field(
        default=None, description="Optional spatial calibration data"
    )
    detections: List[DetectionItem] = Field(
        default_factory=list, description="Array of detected defects"
    )
    processing_metadata: Optional[ProcessingMetadata] = Field(
        default=None, description="Vision pipeline performance metadata"
    )
