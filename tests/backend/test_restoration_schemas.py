"""Unit tests for RestorationResult schema contract."""

import pytest
from pydantic import ValidationError

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


def test_valid_restoration_result() -> None:
    """Verify valid RestorationResult data model instantiation and serialization."""
    result = RestorationResult(
        restoration_strategy=RestorationStrategy.MINIMAL_STABILIZATION,
        prioritized_actions=[
            PrioritizedAction(
                step=1,
                phase=ActionPhase.PHASE_1_IMMEDIATE_STABILIZATION,
                action_title="Vegetation root desiccation and non-impact extraction",
                target_defect="invasive_ficus_root_growth",
                recommended_technique="Bio-compatible biocide injection followed by dead root pruning",
                material_specification="Ammonium sulfamate or diluted acetic biocidal wash",
                urgency=ActionUrgency.IMMEDIATE,
                preconditions=["Dry weather period", "Temporary structural shoring at archway"],
            ),
            PrioritizedAction(
                step=2,
                phase=ActionPhase.PHASE_3_MASONRY_AND_IKS_CONSOLIDATION,
                action_title="Traditional lime-surkhi repointing of open joints",
                target_defect="mortar_washout_and_open_joints",
                recommended_technique="Deep rakeout (2x joint width) and flush pointing",
                material_specification="1:2 slaked fat lime to pulverized surkhi with methi extract",
                urgency=ActionUrgency.HIGH,
            ),
        ],
        incompatible_practices=[
            IncompatiblePractice(
                prohibited_action="Portland Cement pointing or gunite spraying",
                failure_mechanism="Creates vapor barrier leading to sub-surface spalling and salt entrapment",
                severity=IncompatibleSeverity.DESTRUCTIVE,
            )
        ],
        iks_guidelines=IKSGuidelines(
            traditional_mortar_recipe="1 part slaked fat lime putty aged 90 days : 2 parts washed surkhi (brick dust) : 0.05 parts fermented jaggery & methi mucilage",
            craftsmanship_references=[
                "Brihat Samhita chapter on Udakargala (Water Architecture)",
                "Aparajitaprccha treatise on stepwell masonry",
            ],
            seasonal_curing_rules="Apply wet-jute wraps for minimum 21 days; strictly avoid application during peak frost or dry scorching winds.",
        ),
    )

    data = result.model_dump(mode="json")
    assert data["restoration_strategy"] == "minimal_stabilization"
    assert len(data["prioritized_actions"]) == 2
    assert data["prioritized_actions"][0]["step"] == 1
    assert data["iks_guidelines"]["traditional_mortar_recipe"] is not None


def test_prioritized_action_step_less_than_one_fails() -> None:
    """Verify sequence step must be >= 1."""
    with pytest.raises(ValidationError):
        PrioritizedAction(
            step=0,  # Invalid: ge=1 required
            phase=ActionPhase.PHASE_1_IMMEDIATE_STABILIZATION,
            action_title="Test Action",
            target_defect="Test Defect",
            recommended_technique="Test Technique",
            material_specification="Test Material",
            urgency=ActionUrgency.IMMEDIATE,
        )


def test_restoration_missing_iks_guidelines_fails() -> None:
    """Verify failure when iks_guidelines is omitted."""
    with pytest.raises(ValidationError):
        RestorationResult.model_validate(
            {
                "restoration_strategy": "minimal_stabilization",
                "prioritized_actions": [],
                "incompatible_practices": [],
            }
        )
