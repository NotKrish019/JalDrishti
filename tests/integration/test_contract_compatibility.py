"""Integration contract tests verifying bidirectional compatibility between

Pydantic backend schemas and shared Draft 2020-12 JSON schemas in /contracts.

Maintained by Swastik Parmar (Backend / Integration Engineer).
Ensures zero contract divergence between Vision, Engineering, Backend, and Frontend.
"""

import json
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
import pytest
from pydantic import ValidationError as PydanticValidationError

from backend.app.schemas.analysis import (
    AnalysisMetadata,
    AnalysisResult,
    PipelineStatus,
    StructureInfo,
    StructureTypeEnum,
)
from backend.app.schemas.engineering import (
    DeductionUrgency,
    EngineeringResult,
    RootCauseDeduction,
    ScoreMetric,
    SubScores,
)
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
    ProcessingMetadata,
    RelativeSeverity,
    ScaleReference,
    StructureType,
    VisionResult,
)
from backend.app.utils.contracts import load_json_schema, validate_model_against_contract


def test_vision_result_validates_against_json_schema() -> None:
    """Verify VisionResult serialization strictly validates against vision_result.schema.json."""
    vision = VisionResult(
        structure_type=StructureType.BAOLI,
        image_dimensions=ImageDimensions(width_pixels=2048, height_pixels=1536),
        scale_reference=ScaleReference(
            calibrated=True,
            pixels_per_millimeter=1.85,
            method="arch_span_reference",
        ),
        detections=[
            DetectionItem(
                class_name="crack",
                confidence=0.89,
                bounding_box=[120.0, 340.0, 560.0, 780.0],
                segmentation_mask_reference="rle/mask_001.json",
                pixel_area=1420.5,
                coverage_ratio=0.045,
                component_count=2,
                total_length_pixels=230.4,
                largest_component_length_pixels=180.2,
                relative_severity=RelativeSeverity.MODERATE,
            )
        ],
        processing_metadata=ProcessingMetadata(
            inference_latency_ms=185.0,
            model_version="baoli-yolo-v8x-0.1.0",
        ),
    )

    validate_model_against_contract(vision, "vision_result.schema.json")


def test_engineering_result_validates_against_json_schema() -> None:
    """Verify EngineeringResult serialization strictly validates against engineering_result.schema.json."""
    eng = EngineeringResult(
        visual_condition_score=ScoreMetric(
            value=72.0,
            scale_min=0.0,
            scale_max=100.0,
            method="deterministic_weighted_density",
            confidence=0.88,
            limitations=["Evaluates visible surfaces only"],
        ),
        water_functionality_score=ScoreMetric(
            value=55.0,
            scale_min=0.0,
            scale_max=100.0,
            method="hydrological_continuity_index",
            confidence=0.76,
            limitations=["Assumes seasonal water table elevation"],
        ),
        restoration_priority_score=ScoreMetric(
            value=81.0,
            scale_min=0.0,
            scale_max=100.0,
            method="triage_matrix_synthesis",
            confidence=0.84,
            limitations=["Prototype triage score, non-statutory"],
        ),
        sub_scores=SubScores(
            vegetation_intrusion_index=ScoreMetric(
                value=65.0,
                scale_min=0.0,
                scale_max=100.0,
                method="biomass_density",
                confidence=0.9,
                limitations=["Visual foliage index"],
            )
        ),
        root_cause_analysis=[
            RootCauseDeduction(
                finding="Spalling at base tier ashlar masonry",
                probable_cause="Capillary rising damp and salt efflorescence crystallization",
                evidence_rules=["RULE_RISING_DAMP_01"],
                urgency=DeductionUrgency.HIGH,
            )
        ],
    )

    validate_model_against_contract(eng, "engineering_result.schema.json")


def test_material_compatibility_validates_against_json_schema() -> None:
    """Verify MaterialCompatibilityResult strictly validates against material_compatibility.schema.json."""
    mat = MaterialCompatibilityResult(
        original_material="sandstone_dholpur",
        original_material_confidence=0.85,
        verification_required=True,
        recommended_tests=[
            "Petrographic thin section analysis",
            "Capillary water absorption coefficient (Karsten tube)",
        ],
        candidate_interventions=[
            CandidateIntervention(
                intervention_material="slaked_lime_putty_mortar",
                compatibility_score=91.0,
                compatibility_dimensions=CompatibilityDimensions(
                    mechanical=8.8,
                    moisture=9.4,
                    thermal=8.9,
                    chemical=9.5,
                    reversibility=9.2,
                    heritage=10.0,
                    visual=9.0,
                ),
                recommendation=CompatibilityRecommendation.STRONGLY_RECOMMENDED,
                warnings=[],
            )
        ],
    )

    validate_model_against_contract(mat, "material_compatibility.schema.json")


def test_restoration_result_validates_against_json_schema() -> None:
    """Verify RestorationResult strictly validates against restoration_result.schema.json."""
    restoration = RestorationResult(
        restoration_strategy=RestorationStrategy.MINIMAL_STABILIZATION,
        prioritized_actions=[
            PrioritizedAction(
                step=1,
                phase=ActionPhase.PHASE_1_IMMEDIATE_STABILIZATION,
                action_title="Temporary structural shoring at west arch",
                target_defect="shear_crack_lintel",
                recommended_technique="Non-invasive wooden cribbing",
                material_specification="Treated structural timber",
                urgency=ActionUrgency.IMMEDIATE,
            )
        ],
        incompatible_practices=[
            IncompatiblePractice(
                prohibited_action="Portland cement pointing",
                failure_mechanism="Induces differential thermal stress and trapped moisture",
                severity=IncompatibleSeverity.DESTRUCTIVE,
            )
        ],
        iks_guidelines=IKSGuidelines(
            traditional_mortar_recipe="1 part fat lime putty : 2 parts washed surkhi : herbal admixture",
            craftsmanship_references=["Aparajitaprccha stepwell treatises"],
            seasonal_curing_rules="Moist jute sacking curing for 28 days",
        ),
    )

    validate_model_against_contract(restoration, "restoration_result.schema.json")


def test_analysis_result_validates_against_json_schema() -> None:
    """Verify top-level AnalysisResult strictly validates against analysis.schema.json."""
    schema = load_json_schema("analysis.schema.json")
    validator = Draft202012Validator(schema)

    analysis = AnalysisResult(
        project_version="0.1.0",
        structure=StructureInfo(
            type=StructureTypeEnum.BAOLI,
            name="Chand Baori",
            region="Abhaneri, Rajasthan",
            source_images=["data/raw/chand_baori_main.jpg"],
        ),
        vision={
            "structure_type": "baoli",
            "image_dimensions": {"width_pixels": 1920, "height_pixels": 1080},
            "detections": [],
        },
        visual_condition={
            "value": 75.0,
            "scale_min": 0.0,
            "scale_max": 100.0,
            "method": "visual_density_scoring",
            "confidence": 0.85,
            "limitations": ["Visual only"],
        },
        water_functionality={
            "value": 60.0,
            "scale_min": 0.0,
            "scale_max": 100.0,
            "method": "catchment_connectivity",
            "confidence": 0.80,
            "limitations": ["Visual evidence only"],
        },
        material={
            "original_material": "sandstone_dholpur",
            "original_material_confidence": 0.85,
            "verification_required": True,
            "candidate_interventions": [],
        },
        root_cause={
            "findings": ["Mortar erosion due to water level fluctuations"],
        },
        restoration={
            "restoration_strategy": "minimal_stabilization",
            "prioritized_actions": [],
            "incompatible_practices": [],
            "iks_guidelines": {
                "traditional_mortar_recipe": "Lime + surkhi",
                "craftsmanship_references": [],
                "seasonal_curing_rules": "Wet-jute curing",
            },
        },
        metadata=AnalysisMetadata(
            created_at="2026-10-08T12:00:00Z",
            pipeline_status=PipelineStatus.COMPLETED,
            orchestrated_by="Swastik Parmar (Backend Orchestrator)",
        ),
    )

    data = analysis.model_dump(mode="json", exclude_none=True)
    validator.validate(data)


def test_fully_typed_analysis_result_validates_against_json_schema() -> None:
    """Verify AnalysisResult containing fully-typed nested Pydantic models validates against analysis.schema.json."""
    vision = VisionResult(
        structure_type=StructureType.KUND,
        image_dimensions=ImageDimensions(width_pixels=3840, height_pixels=2160),
        detections=[
            DetectionItem(
                class_name="vegetation",
                confidence=0.95,
                bounding_box=[500.0, 600.0, 900.0, 1100.0],
                pixel_area=25000.0,
                coverage_ratio=0.03,
                component_count=4,
            )
        ],
    )

    visual_condition = ScoreMetric(
        value=58.0,
        scale_min=0.0,
        scale_max=100.0,
        method="morphological_defect_index",
        confidence=0.89,
        limitations=["Surface visible masonry only"],
    )

    water_functionality = ScoreMetric(
        value=72.0,
        scale_min=0.0,
        scale_max=100.0,
        method="aquifer_recharge_potential",
        confidence=0.81,
        limitations=["Historical seasonal precipitation data assumed"],
    )

    material = MaterialCompatibilityResult(
        original_material="basalt_rubble_masonry",
        original_material_confidence=0.78,
        verification_required=True,
        candidate_interventions=[
            CandidateIntervention(
                intervention_material="hydraulic_lime_grout",
                compatibility_score=88.0,
                compatibility_dimensions=CompatibilityDimensions(
                    mechanical=8.5,
                    moisture=9.0,
                    thermal=8.7,
                    chemical=9.1,
                    reversibility=8.8,
                    heritage=9.5,
                    visual=8.6,
                ),
                recommendation=CompatibilityRecommendation.RECOMMENDED,
                warnings=[],
            )
        ],
    )

    restoration = RestorationResult(
        restoration_strategy=RestorationStrategy.HYDROLOGICAL_REVIVAL,
        prioritized_actions=[
            PrioritizedAction(
                step=1,
                phase=ActionPhase.PHASE_2_HYDROLOGICAL_REMEDIATION,
                action_title="De-silt catchment channels",
                target_defect="siltation_blockage",
                recommended_technique="Manual dredging without heavy machinery",
                material_specification="Unconsolidated sediment removal",
                urgency=ActionUrgency.HIGH,
            )
        ],
        incompatible_practices=[
            IncompatiblePractice(
                prohibited_action="Concrete floor lining",
                failure_mechanism="Prevents natural groundwater percolation into stepwell aquifer",
                severity=IncompatibleSeverity.DESTRUCTIVE,
            )
        ],
        iks_guidelines=IKSGuidelines(
            traditional_mortar_recipe="Hydraulic lime with washed sand and herbal extract",
            craftsmanship_references=["Manasara Shilpa Shastra"],
            seasonal_curing_rules="28-day moist curing avoiding dry hot winds",
        ),
    )

    analysis = AnalysisResult(
        project_version="0.1.0",
        structure=StructureInfo(
            type=StructureTypeEnum.KUND,
            name="Panna Meena ka Kund",
            region="Amer, Rajasthan",
            source_images=["data/raw/panna_meena_01.jpg"],
        ),
        vision=vision,
        visual_condition=visual_condition,
        water_functionality=water_functionality,
        material=material,
        root_cause={
            "diagnosis": "Sedimentation ingress and invasive ficus germination in joint cavities",
            "mechanisms": ["siltation", "biomass_expansion"],
        },
        restoration=restoration,
        metadata=AnalysisMetadata(
            created_at="2026-10-08T12:00:00Z",
            pipeline_status=PipelineStatus.COMPLETED,
            orchestrated_by="Swastik Parmar (Backend Orchestrator)",
        ),
    )

    validate_model_against_contract(analysis, "analysis.schema.json")


def test_round_trip_serialization() -> None:
    """Verify round-trip JSON string -> Pydantic Model -> serialized dict matches contract."""
    raw_json = json.dumps(
        {
            "structure_type": "baoli",
            "image_dimensions": {"width_pixels": 1280, "height_pixels": 720},
            "detections": [
                {
                    "class_name": "spalling",
                    "confidence": 0.82,
                    "bounding_box": [50.0, 60.0, 180.0, 220.0],
                    "pixel_area": 890.0,
                    "coverage_ratio": 0.009,
                    "component_count": 1,
                }
            ],
        }
    )

    model = VisionResult.model_validate_json(raw_json)
    assert model.structure_type == StructureType.BAOLI
    assert len(model.detections) == 1

    validate_model_against_contract(model, "vision_result.schema.json")


def test_invalid_contract_rejected_by_both() -> None:
    """Verify invalid structures fail both Pydantic and JSON Schema validation."""
    invalid_data = {
        "structure_type": "invalid_monument_type",
        "image_dimensions": {"width_pixels": 0, "height_pixels": -10},
        "detections": [],
    }

    # Fails Pydantic validation
    with pytest.raises(PydanticValidationError):
        VisionResult.model_validate(invalid_data)

    # Fails JSON Schema validation
    schema = load_json_schema("vision_result.schema.json")
    with pytest.raises(JsonSchemaValidationError):
        Draft202012Validator(schema).validate(invalid_data)
