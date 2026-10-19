"""Unit and contract validation tests for Root Cause, Water Functionality, and Restoration Engine (Phase 3).

Owner: Kirti Antil (IKS / Material Compatibility / Conservation Engineering Lead)
"""

import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator

from engineering.scoring.visual_condition import VisualConditionScorer, calculate_visual_condition
from engineering.water_functionality.water_scorer import WaterFunctionalityScorer, calculate_water_functionality
from engineering.root_cause.deduction_rules import RootCauseDeductionEngine, deduce_root_causes
from engineering.restoration.restoration_planner import RestorationPlanningEngine, plan_restoration
from engineering.assessment import EngineeringAssessmentEngine, run_engineering_assessment


WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
ENGINEERING_RESULT_CONTRACT = WORKSPACE_ROOT / "contracts" / "engineering_result.schema.json"
RESTORATION_RESULT_CONTRACT = WORKSPACE_ROOT / "contracts" / "restoration_result.schema.json"


@pytest.fixture(scope="module")
def engineering_contract_schema() -> dict:
    with open(ENGINEERING_RESULT_CONTRACT, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def restoration_contract_schema() -> dict:
    with open(RESTORATION_RESULT_CONTRACT, "r", encoding="utf-8") as f:
        return json.load(f)


class TestVisualConditionScoring:
    """Validate deterministic condition scoring and deduct mechanics."""

    def test_pristine_condition(self) -> None:
        res = calculate_visual_condition()
        score = res["visual_condition_score"]
        assert score["value"] == 100.0
        assert score["scale_min"] == 0.0
        assert score["scale_max"] == 100.0
        assert len(score["limitations"]) >= 1

    def test_degraded_condition_with_vision_detections(self) -> None:
        detections = [
            {"class_name": "crack", "coverage_ratio": 0.15, "relative_severity": "severe", "confidence": 0.85},
            {"class_name": "vegetation_root_intrusion", "coverage_ratio": 0.10, "relative_severity": "moderate", "confidence": 0.80},
            {"class_name": "spalling", "coverage_ratio": 0.08, "relative_severity": "low", "confidence": 0.90},
        ]
        res = calculate_visual_condition(detections=detections)
        score = res["visual_condition_score"]
        assert 20.0 <= score["value"] <= 60.0
        assert res["sub_scores"]["vegetation_intrusion_index"]["value"] < 100.0
        assert res["sub_scores"]["masonry_integrity_index"]["value"] < 100.0

    def test_missing_data_defaults(self) -> None:
        res = calculate_visual_condition(detections=[])
        assert res["visual_condition_score"]["value"] == 100.0
        assert res["visual_condition_score"]["confidence"] > 0.5


class TestWaterFunctionalityScoring:
    """Validate hydrological viability calculations."""

    def test_optimal_hydrology(self) -> None:
        res = calculate_water_functionality(
            inlet_condition="clear",
            outlet_condition="clear",
            siltation_level="none",
            water_presence="perennial_clean",
            catchment_condition="intact",
        )
        score = res["water_functionality_score"]
        assert score["value"] == 100.0
        assert res["sub_scores"]["siltation_obstruction_index"]["value"] == 100.0

    def test_severely_impaired_hydrology(self) -> None:
        res = calculate_water_functionality(
            inlet_condition="choked",
            outlet_condition="choked",
            siltation_level="severe",
            water_presence="stagnant",
            catchment_condition="severely_encroached",
        )
        score = res["water_functionality_score"]
        assert score["value"] < 25.0
        assert res["sub_scores"]["siltation_obstruction_index"]["value"] <= 15.0

    def test_unknown_hydrology_confidence_penalty(self) -> None:
        res = calculate_water_functionality()
        score = res["water_functionality_score"]
        assert score["confidence"] <= 0.60
        assert len(score["limitations"]) >= 1


class TestRootCauseDeduction:
    """Validate diagnostic reasoning trees and hypothesis formulation."""

    def test_vegetation_intrusion_chain(self) -> None:
        causes = deduce_root_causes(vegetation_burden=0.18, dislodgement_burden=0.12)
        veg_cause = next(c for c in causes if "vegetation" in c["finding"].lower())
        assert veg_cause["urgency"] in ["high", "critical"]
        assert "VEGETATION -> ROOT INTRUSION" in " ".join(veg_cause["evidence_rules"])
        assert "contributing factor" in veg_cause["probable_cause"].lower()

    def test_inflow_starvation_chain(self) -> None:
        causes = deduce_root_causes(inlet_condition="choked", catchment_condition="severely_encroached")
        inlet_cause = next(c for c in causes if "inflow" in c["finding"].lower())
        assert inlet_cause["urgency"] in ["high", "critical"]
        assert "BLOCKED INLET" in " ".join(inlet_cause["evidence_rules"])

    def test_cement_repair_damage_chain(self) -> None:
        causes = deduce_root_causes(recent_repair_type="portland_cement_opc", spalling_burden=0.10)
        cement_cause = next(c for c in causes if "cement" in c["finding"].lower())
        assert cement_cause["urgency"] == "critical"
        assert "VAPOR BARRIER" in " ".join(cement_cause["evidence_rules"])

    def test_no_critical_defects_returns_routine_baseline(self) -> None:
        causes = deduce_root_causes(crack_burden=0.01, vegetation_burden=0.01)
        assert len(causes) == 1
        assert causes[0]["urgency"] == "low"
        assert causes[0]["expert_review_required"] is False
        assert "preventative" in causes[0]["probable_cause"].lower()

    def test_root_cause_transparency_and_evidence_chain(self) -> None:
        """Verify that observed indicators are strictly decoupled from inferred mechanisms and investigations."""
        causes = deduce_root_causes(
            crack_burden=0.15,
            vegetation_burden=0.10,
            siltation_level="severe",
            recent_repair_type="portland_cement_opc",
        )
        assert len(causes) >= 3
        for c in causes:
            assert "finding" in c
            assert "observed_indicator" in c
            assert "probable_cause" in c
            assert "evidence_rules" in c
            assert "additional_investigation_required" in c
            assert len(c["additional_investigation_required"]) >= 1
            assert "supporting_sources" in c
            assert len(c["supporting_sources"]) >= 1
            assert "uncertainty_note" in c
            assert "expert_review_required" in c

    def test_structural_cracking_triggers_expert_review_flag(self) -> None:
        causes = deduce_root_causes(crack_burden=0.18)
        crack_cause = next(c for c in causes if "cracking" in c["finding"].lower())
        assert crack_cause["expert_review_required"] is True
        assert "structural" in crack_cause["expert_specialty"].lower()
        assert crack_cause["urgency"] in ["high", "critical"]
        assert any("geotechnical" in inv.lower() or "tell-tale" in inv.lower() for inv in crack_cause["additional_investigation_required"])



class TestRestorationPlanningEngineContract:
    """Validate phased restoration outputs against contracts/restoration_result.schema.json."""

    def test_plan_restoration_conforms_to_schema(self, restoration_contract_schema: dict) -> None:
        payload = plan_restoration(
            structure_type="baoli",
            visual_condition_score=45.0,
            water_functionality_score=35.0,
            crack_burden=0.15,
            vegetation_burden=0.20,
            spalling_burden=0.10,
            siltation_level="severe",
            inlet_condition="choked",
            inferred_material="hydraulic_lime_mortar",
        )

        validator = Draft202012Validator(restoration_contract_schema)
        errors = list(validator.iter_errors(payload))
        assert len(errors) == 0, f"Restoration result contract errors: {[e.message for e in errors]}"

        # Check phased sequence
        phases = [a["phase"] for a in payload["prioritized_actions"]]
        assert "phase_1_immediate_stabilization" in phases
        assert "phase_2_hydrological_remediation" in phases
        assert "phase_3_masonry_and_iks_consolidation" in phases
        assert "phase_4_long_term_monitoring" in phases

        # Check step ordering
        steps = [a["step"] for a in payload["prioritized_actions"]]
        assert steps == sorted(steps)

        # Check incompatible practices
        incompat = payload["incompatible_practices"]
        assert len(incompat) >= 2
        prohibited_names = [p["prohibited_action"].lower() for p in incompat]
        assert any("portland cement" in p for p in prohibited_names)
        assert any("acrylic" in p or "epoxy" in p for p in prohibited_names)

        # Check IKS guidelines
        iks = payload["iks_guidelines"]
        assert "surkhi" in iks["traditional_mortar_recipe"].lower()
        assert len(iks["craftsmanship_references"]) >= 2
        assert "curing" in iks["seasonal_curing_rules"].lower()


class TestUnifiedEngineeringAssessmentContract:
    """Validate unified assessment output against contracts/engineering_result.schema.json."""

    def test_assessment_conforms_to_schema(self, engineering_contract_schema: dict) -> None:
        payload = run_engineering_assessment(
            structure_type="vav",
            crack_burden=0.12,
            vegetation_burden=0.15,
            spalling_burden=0.08,
            inlet_condition="partially_blocked",
            siltation_level="moderate",
            water_presence="stagnant",
        )

        validator = Draft202012Validator(engineering_contract_schema)
        errors = list(validator.iter_errors(payload))
        assert len(errors) == 0, f"Engineering result contract errors: {[e.message for e in errors]}"

        # Check top-level required fields
        assert "visual_condition_score" in payload
        assert "water_functionality_score" in payload
        assert "restoration_priority_score" in payload
        assert "engineering_disclaimer" in payload

        # Check scores bounds
        assert 0.0 <= payload["visual_condition_score"]["value"] <= 100.0
        assert 0.0 <= payload["water_functionality_score"]["value"] <= 100.0
        assert 0.0 <= payload["restoration_priority_score"]["value"] <= 100.0

        # Check disclaimer
        disclaimer = payload["engineering_disclaimer"]
        assert "certified structural engineering" in disclaimer.lower() or "prototype decision-support" in disclaimer.lower()
