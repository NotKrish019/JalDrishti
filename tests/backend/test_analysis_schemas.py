"""Unit tests for top-level AnalysisResult schema contract."""

import pytest
from pydantic import ValidationError

from backend.app.schemas.analysis import (
    AnalysisMetadata,
    AnalysisResult,
    PipelineStatus,
    StructureInfo,
    StructureTypeEnum,
)
from backend.app.schemas.engineering import EngineeringResult, ScoreMetric
from backend.app.schemas.material import (
    CandidateIntervention,
    CompatibilityDimensions,
    CompatibilityRecommendation,
    MaterialCompatibilityResult,
)
from backend.app.schemas.restoration import (
    ActionPhase,
    ActionUrgency,
    IKSGuidelines,
    IncompatiblePractice,
    IncompatibleSeverity,
    PrioritizedAction,
    RestorationResult,
    RestorationStrategy,
)
from backend.app.schemas.vision import (
    DetectionItem,
    ImageDimensions,
    StructureType,
    VisionResult,
)


def create_sample_analysis_result() -> AnalysisResult:
    """Helper to build a complete, strongly-typed AnalysisResult."""
    vision_result = VisionResult(
        structure_type=StructureType.BAOLI,
        image_dimensions=ImageDimensions(width_pixels=1920, height_pixels=1080),
        detections=[
            DetectionItem(
                class_name="crack",
                confidence=0.91,
                bounding_box=[100.0, 150.0, 200.0, 250.0],
                pixel_area=320.0,
                coverage_ratio=0.01,
                component_count=1,
            )
        ],
    )

    visual_condition = ScoreMetric(
        value=65.0,
        scale_min=0.0,
        scale_max=100.0,
        method="defect_density_index",
        confidence=0.85,
        limitations=["Surface visible inspection only"],
    )

    water_functionality = ScoreMetric(
        value=40.0,
        scale_min=0.0,
        scale_max=100.0,
        method="catchment_obstruction_ratio",
        confidence=0.78,
        limitations=["Inferred catchment from dry imagery"],
    )

    material = MaterialCompatibilityResult(
        original_material="lime_mortar_hydraulic",
        original_material_confidence=0.8,
        verification_required=True,
        candidate_interventions=[
            CandidateIntervention(
                intervention_material="surkhi_lime_mortar",
                compatibility_score=92.0,
                compatibility_dimensions=CompatibilityDimensions(
                    mechanical=9.0,
                    moisture=9.2,
                    thermal=9.0,
                    chemical=9.1,
                    reversibility=9.0,
                    heritage=10.0,
                    visual=9.5,
                ),
                recommendation=CompatibilityRecommendation.STRONGLY_RECOMMENDED,
                warnings=[],
            )
        ],
    )

    restoration = RestorationResult(
        restoration_strategy=RestorationStrategy.MINIMAL_STABILIZATION,
        prioritized_actions=[
            PrioritizedAction(
                step=1,
                phase=ActionPhase.PHASE_1_IMMEDIATE_STABILIZATION,
                action_title="Stabilize fractured arch lintel",
                target_defect="structural_crack",
                recommended_technique="Temporary wooden shoring and propping",
                material_specification="Sal wood timber shores",
                urgency=ActionUrgency.IMMEDIATE,
            )
        ],
        incompatible_practices=[
            IncompatiblePractice(
                prohibited_action="Cement gunite spray",
                failure_mechanism="Moisture entrapment and stone spalling",
                severity=IncompatibleSeverity.DESTRUCTIVE,
            )
        ],
        iks_guidelines=IKSGuidelines(
            traditional_mortar_recipe="Slaked lime putty + surkhi + organic additives",
            craftsmanship_references=["Aparajitaprccha"],
            seasonal_curing_rules="21-day continuous moist curing with hessian cloth",
        ),
    )

    return AnalysisResult(
        project_version="0.1.0",
        structure=StructureInfo(
            type=StructureTypeEnum.BAOLI,
            name="Agrasen ki Baoli",
            region="Delhi, India",
            source_images=["data/raw/agrasen_01.jpg"],
        ),
        vision=vision_result,
        visual_condition=visual_condition,
        water_functionality=water_functionality,
        material=material,
        root_cause={
            "primary_degradation_mechanism": "Vegetation wedging and groundwater drawdown",
            "confidence": 0.82,
        },
        restoration=restoration,
        metadata=AnalysisMetadata(
            created_at="2026-10-08T12:00:00Z",
            pipeline_status=PipelineStatus.COMPLETED,
            orchestrated_by="Swastik Parmar (Backend Orchestrator)",
        ),
    )


def test_valid_analysis_result_serialization() -> None:
    """Verify complete AnalysisResult instance builds and serializes cleanly."""
    analysis = create_sample_analysis_result()
    payload = analysis.model_dump(mode="json")

    assert payload["project_version"] == "0.1.0"
    assert payload["structure"]["type"] == "baoli"
    assert "vision" in payload
    assert "visual_condition" in payload
    assert "water_functionality" in payload
    assert "material" in payload
    assert "root_cause" in payload
    assert "restoration" in payload
    assert "metadata" in payload

    assert payload["metadata"]["pipeline_status"] == "completed"


def test_structure_empty_images_fails() -> None:
    """Verify structure must have at least one source image."""
    with pytest.raises(ValidationError):
        StructureInfo(
            type=StructureTypeEnum.BAOLI,
            source_images=[],  # min_length=1
        )


def test_analysis_missing_required_section_fails() -> None:
    """Verify missing required top-level section fails validation."""
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(
            {
                "project_version": "0.1.0",
                "structure": {
                    "type": "baoli",
                    "source_images": ["img1.jpg"],
                },
                # Missing vision, visual_condition, etc.
            }
        )
