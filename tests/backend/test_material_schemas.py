"""Unit tests for MaterialCompatibilityResult schema contract."""

import pytest
from pydantic import ValidationError

from backend.app.schemas.material import (
    CandidateIntervention,
    CompatibilityDimensions,
    CompatibilityRecommendation,
    MaterialCompatibilityResult,
)


def test_valid_material_compatibility_result() -> None:
    """Verify valid MaterialCompatibilityResult data model instantiation and serialization."""
    result = MaterialCompatibilityResult(
        original_material="lime_mortar_hydraulic",
        original_material_confidence=0.72,
        verification_required=True,
        recommended_tests=[
            "Thin-section petrography",
            "Acid digestion binder-to-aggregate ratio",
        ],
        candidate_interventions=[
            CandidateIntervention(
                intervention_material="surkhi_lime_mortar_1_2",
                compatibility_score=94.5,
                compatibility_dimensions=CompatibilityDimensions(
                    mechanical=9.2,
                    moisture=9.5,
                    thermal=9.0,
                    chemical=9.4,
                    reversibility=9.0,
                    heritage=10.0,
                    visual=9.5,
                ),
                recommendation=CompatibilityRecommendation.STRONGLY_RECOMMENDED,
                warnings=[],
            ),
            CandidateIntervention(
                intervention_material="portland_cement_opc_53",
                compatibility_score=15.0,
                compatibility_dimensions=CompatibilityDimensions(
                    mechanical=1.5,
                    moisture=1.0,
                    thermal=2.0,
                    chemical=2.5,
                    reversibility=1.0,
                    heritage=1.0,
                    visual=2.0,
                ),
                recommendation=CompatibilityRecommendation.PROHIBITED_INCOMPATIBLE,
                warnings=[
                    "High rigidity causes preferential fracture of historic stone",
                    "Impermeability traps moisture inducing accelerated salt crystallization",
                ],
            ),
        ],
    )

    data = result.model_dump(mode="json")
    assert data["original_material"] == "lime_mortar_hydraulic"
    assert data["verification_required"] is True
    assert len(data["candidate_interventions"]) == 2
    assert (
        data["candidate_interventions"][0]["recommendation"]
        == "strongly_recommended"
    )


def test_compatibility_dimension_out_of_bounds_fails() -> None:
    """Verify score on 0-10 scale rejects values > 10.0 or < 0.0."""
    with pytest.raises(ValidationError):
        CompatibilityDimensions(
            mechanical=11.0,  # Invalid: > 10.0
            moisture=8.0,
            thermal=8.0,
            chemical=8.0,
            reversibility=8.0,
            heritage=8.0,
            visual=8.0,
        )


def test_material_missing_required_fields_fails() -> None:
    """Verify failure when original_material or confidence missing."""
    with pytest.raises(ValidationError):
        MaterialCompatibilityResult.model_validate(
            {"candidate_interventions": []}
        )
