"""Unit tests for EngineeringResult schema contract."""

import pytest
from pydantic import ValidationError

from backend.app.schemas.engineering import (
    DeductionUrgency,
    EngineeringResult,
    RootCauseDeduction,
    ScoreMetric,
    SubScores,
)


def test_valid_engineering_result() -> None:
    """Verify valid EngineeringResult data model instantiation and serialization."""
    result = EngineeringResult(
        visual_condition_score=ScoreMetric(
            value=62.5,
            scale_min=0.0,
            scale_max=100.0,
            method="weighted_defect_density_v1",
            confidence=0.88,
            limitations=["Visible surface only; subsurface voids unassessed"],
        ),
        water_functionality_score=ScoreMetric(
            value=45.0,
            scale_min=0.0,
            scale_max=100.0,
            method="catchment_siltation_index_v1",
            confidence=0.75,
            limitations=["Dry-season visual assessment without borehole data"],
        ),
        restoration_priority_score=ScoreMetric(
            value=78.0,
            scale_min=0.0,
            scale_max=100.0,
            method="urgency_synthesis_v1",
            confidence=0.82,
            limitations=["Prototype triage score, non-statutory"],
        ),
        sub_scores=SubScores(
            vegetation_intrusion_index=ScoreMetric(
                value=70.0,
                scale_min=0.0,
                scale_max=100.0,
                method="biomass_coverage_v1",
                confidence=0.90,
                limitations=["Root depth inferred from visible trunk girth"],
            )
        ),
        root_cause_analysis=[
            RootCauseDeduction(
                finding="Deep masonry separation at retaining wall L3",
                probable_cause="Hydrostatic pressure due to clogged drainage weep holes",
                evidence_rules=["RULE_WALL_BULGING_01", "RULE_DRAINAGE_DEFICIT_02"],
                urgency=DeductionUrgency.HIGH,
            )
        ],
    )

    data = result.model_dump(mode="json")
    assert data["visual_condition_score"]["value"] == 62.5
    assert data["engineering_disclaimer"] is not None
    assert "prototype" in data["engineering_disclaimer"].lower()
    assert len(data["root_cause_analysis"]) == 1


def test_score_metric_empty_limitations_fails() -> None:
    """Verify limitations array must have at least one element."""
    with pytest.raises(ValidationError):
        ScoreMetric(
            value=50.0,
            scale_min=0.0,
            scale_max=100.0,
            method="simple_average",
            confidence=0.8,
            limitations=[],  # Empty list violates min_length=1
        )


def test_score_metric_confidence_out_of_bounds_fails() -> None:
    """Verify confidence must be in range [0.0, 1.0]."""
    with pytest.raises(ValidationError):
        ScoreMetric(
            value=50.0,
            scale_min=0.0,
            scale_max=100.0,
            method="simple_average",
            confidence=1.1,
            limitations=["None"],
        )


def test_engineering_result_missing_required_scores_fails() -> None:
    """Verify failure when required primary scores are omitted."""
    with pytest.raises(ValidationError):
        EngineeringResult.model_validate({})
