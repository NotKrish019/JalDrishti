"""API request schemas for JalDrishti pipeline endpoints.

Maintained by Swastik Parmar (Backend / Integration Engineer).
Enables typed validation for Vision, Engineering, Material Compatibility,
Restoration, and Unified Analysis API ingestion.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.schemas.vision import (
    DetectionItem,
    ImageDimensions,
    ScaleReference,
    StructureType,
    VisionResult,
)


class EngineeringAssessmentRequest(BaseModel):
    """Request payload for POST /engineering assessment."""

    model_config = ConfigDict(extra="ignore")

    vision: Optional[VisionResult] = Field(
        default=None, description="Optional vision analysis payload containing detected defects"
    )
    structure_type: Optional[StructureType] = Field(
        default=None, description="Typology of target water structure"
    )
    structure_name: Optional[str] = Field(
        default=None, description="Optional monument designation"
    )
    region: Optional[str] = Field(
        default=None, description="Optional geographical territory"
    )
    image_dimensions: Optional[ImageDimensions] = Field(
        default=None, description="Optional explicit image spatial resolution"
    )
    detections: Optional[List[DetectionItem]] = Field(
        default=None, description="Optional direct defect detections list"
    )
    inspection_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Hydrological indicators (inlet_condition, outlet_condition, siltation_level, water_presence, catchment_condition)",
    )
    inferred_material: Optional[str] = Field(
        default=None, description="Historic substrate identifier (e.g. hydraulic_lime_mortar, historic_sandstone)"
    )
    material_confidence: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Photographic identification confidence (capped at 0.85)"
    )
    candidate_materials: Optional[List[str]] = Field(
        default=None, description="Candidate repair mortars or materials to evaluate"
    )
    recent_repair_type: Optional[str] = Field(
        default=None, description="Modern observed repair material (e.g. portland_cement_opc)"
    )

    @model_validator(mode="after")
    def validate_input_source(self) -> "EngineeringAssessmentRequest":
        if self.vision is None and self.structure_type is None:
            raise ValueError(
                "Either 'vision' payload or 'structure_type' must be provided for engineering assessment."
            )
        return self


class MaterialCompatibilityRequest(BaseModel):
    """Request payload for POST /material-compatibility evaluation."""

    model_config = ConfigDict(extra="ignore")

    original_material: Optional[str] = Field(
        default="hydraulic_lime_mortar",
        description="Identified or inferred original historic substrate (e.g. hydraulic_lime_mortar, historic_sandstone)",
    )
    candidate_materials: Optional[List[str]] = Field(
        default=None,
        description="List of candidate intervention mortars/materials to evaluate against substrate",
    )
    original_material_confidence: Optional[float] = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Probabilistic confidence of material identification (capped at 0.85 per scientific standard)",
    )
    structure_type: Optional[StructureType] = Field(
        default=None,
        description="Optional structure typology used to infer default substrate if original_material is omitted",
    )


class RestorationPlanRequest(BaseModel):
    """Request payload for POST /restore conservation planning."""

    model_config = ConfigDict(extra="ignore")

    structure_type: Optional[StructureType] = Field(
        default=StructureType.BAOLI,
        description="Typology of target water structure ('baoli', 'bawari', 'kund', 'vav')",
    )
    visual_condition_score: Optional[float] = Field(
        default=75.0,
        ge=0.0,
        le=100.0,
        description="Visual condition score from engineering assessment (0-100)",
    )
    water_functionality_score: Optional[float] = Field(
        default=60.0,
        ge=0.0,
        le=100.0,
        description="Hydrological functionality score (0-100)",
    )
    crack_burden: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Normalized crack defect burden (0.0 - 1.0)",
    )
    vegetation_burden: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Normalized vegetation defect burden (0.0 - 1.0)",
    )
    spalling_burden: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Normalized stone spalling burden (0.0 - 1.0)",
    )
    dislodgement_burden: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Normalized block dislodgement burden (0.0 - 1.0)",
    )
    siltation_level: Optional[str] = Field(
        default="unknown",
        description="Basin siltation status ('severe', 'moderate', 'low', 'unknown')",
    )
    inlet_condition: Optional[str] = Field(
        default="unknown",
        description="Inlet channel status ('choked', 'broken', 'partially_blocked', 'clear', 'unknown')",
    )
    inferred_material: Optional[str] = Field(
        default="hydraulic_lime_mortar",
        description="Historic substrate formulation",
    )
    root_causes: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Deductions from root-cause analysis",
    )


class AnalysisPipelineRequest(BaseModel):
    """Request payload for POST /analyze unified pipeline orchestration."""

    model_config = ConfigDict(extra="ignore")

    structure_type: StructureType = Field(
        default=StructureType.BAOLI, description="Typology of target water structure"
    )
    name: Optional[str] = Field(
        default="Heritage Baoli", description="Site or monument designation"
    )
    region: Optional[str] = Field(
        default="Northern India", description="Geographical territory"
    )
    source_images: List[str] = Field(
        default_factory=lambda: ["survey_image_01.jpg"],
        min_length=1,
        description="URIs or file identifiers for inspected imagery",
    )
    image_dimensions: Optional[ImageDimensions] = Field(
        default=None, description="Optional explicit image spatial resolution"
    )
    scale_reference: Optional[ScaleReference] = Field(
        default=None, description="Optional calibrated scale reference"
    )
    detections: Optional[List[DetectionItem]] = Field(
        default=None, description="Optional defect annotations or surveyor entries"
    )
    inspection_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional hydrological inspection indicators",
    )
    inferred_material: Optional[str] = Field(
        default=None,
        description="Optional substrate specification (e.g. 'hydraulic_lime_mortar')",
    )
    material_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional substrate identification confidence",
    )
    candidate_materials: Optional[List[str]] = Field(
        default=None,
        description="Optional custom list of candidate intervention materials to assess",
    )
    recent_repair_type: Optional[str] = Field(
        default=None,
        description="Optional modern repair observed (e.g. 'portland_cement_opc')",
    )
