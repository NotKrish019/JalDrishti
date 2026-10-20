"""Comprehensive Phase 4 Engineering Validation and Integration Readiness Test Suite.

Verifies that the Kirti-owned module provides stable interfaces, robust input handling,
graceful fallback for missing/insufficient data, probabilistic material identification,
and 100% schema compatibility with all system contracts.

Owner: Kirti Antil (IKS / Material Compatibility / Conservation Engineering Lead)
"""

import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator

from engineering import (
    analyze_heritage_structure,
    get_structure,
    list_structures,
    get_source,
    evaluate_compatibility,
    run_engineering_assessment,
    plan_restoration,
    ConservationEngineeringService,
)


WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACTS_DIR = WORKSPACE_ROOT / "contracts"


@pytest.fixture(scope="module")
def engineering_schema() -> dict:
    with open(CONTRACTS_DIR / "engineering_result.schema.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def material_schema() -> dict:
    with open(CONTRACTS_DIR / "material_compatibility.schema.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def restoration_schema() -> dict:
    with open(CONTRACTS_DIR / "restoration_result.schema.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def analysis_schema() -> dict:
    with open(CONTRACTS_DIR / "analysis.schema.json", "r", encoding="utf-8") as f:
        return json.load(f)


class TestStableInterfacesAndExports:
    """Verify that all required public interfaces exist and are callable."""

    def test_top_level_exports(self) -> None:
        assert callable(analyze_heritage_structure)
        assert callable(get_structure)
        assert callable(list_structures)
        assert callable(get_source)
        assert callable(evaluate_compatibility)
        assert callable(run_engineering_assessment)
        assert callable(plan_restoration)

    def test_knowledge_lookup_interface(self) -> None:
        structures = list_structures()
        assert len(structures) >= 4
        baoli = get_structure("baoli")
        assert baoli["id"] == "baoli"
        source = get_source("SRC_ASI_CONSERVATION_MANUAL_2020")
        assert source is not None
        assert "ASI" in source["publisher"] or "Archaeological" in source["publisher"]


class TestContractConformanceAcrossAllTypologies:
    """Verify that every supported typology generates schema-valid outputs across all contracts."""

    @pytest.mark.parametrize("typology", ["baoli", "bawari", "kund", "vav"])
    def test_full_analysis_schema_validity(
        self,
        typology: str,
        engineering_schema: dict,
        material_schema: dict,
        restoration_schema: dict,
    ) -> None:
        result = analyze_heritage_structure(
            structure_type=typology,
            vision_data={
                "structure_type": typology,
                "image_dimensions": {"width_pixels": 1920, "height_pixels": 1080},
                "detections": [
                    {
                        "class_name": "crack",
                        "confidence": 0.88,
                        "bounding_box": [100.0, 200.0, 400.0, 500.0],
                        "pixel_area": 12500.0,
                        "coverage_ratio": 0.08,
                        "component_count": 3,
                        "relative_severity": "moderate",
                    },
                    {
                        "class_name": "vegetation_root_intrusion",
                        "confidence": 0.92,
                        "bounding_box": [50.0, 80.0, 300.0, 450.0],
                        "pixel_area": 18000.0,
                        "coverage_ratio": 0.12,
                        "component_count": 2,
                        "relative_severity": "severe",
                    },
                ],
            },
            inspection_data={
                "inlet_condition": "partially_blocked",
                "outlet_condition": "clear",
                "siltation_level": "moderate",
                "water_presence": "stagnant",
                "catchment_condition": "partially_encroached",
            },
        )

        # 1. Validate Engineering Result payload
        eng_validator = Draft202012Validator(engineering_schema)
        eng_errors = list(eng_validator.iter_errors(result["engineering_result"]))
        assert len(eng_errors) == 0, f"Engineering schema error in {typology}: {[e.message for e in eng_errors]}"

        # 2. Validate Material Compatibility payload
        mat_validator = Draft202012Validator(material_schema)
        mat_errors = list(mat_validator.iter_errors(result["material"]))
        assert len(mat_errors) == 0, f"Material schema error in {typology}: {[e.message for e in mat_errors]}"

        # 3. Validate Restoration Result payload
        res_validator = Draft202012Validator(restoration_schema)
        res_errors = list(res_validator.iter_errors(result["restoration"]))
        assert len(res_errors) == 0, f"Restoration schema error in {typology}: {[e.message for e in res_errors]}"

        # 4. Check unified output contract keys
        assert "visual_condition" in result
        assert "water_functionality" in result
        assert "material" in result
        assert "root_cause" in result
        assert "restoration" in result
        assert "warnings" in result
        assert "limitations" in result


class TestResilienceToMissingAndInsufficientData:
    """Verify that missing inputs, empty detections, and uncertain materials are handled cleanly."""

    def test_completely_empty_inputs(self, engineering_schema: dict) -> None:
        """Calling analyze_heritage_structure with no arguments must not crash."""
        result = analyze_heritage_structure()
        assert result is not None
        assert result["structure_type"] == "unknown"
        assert result["visual_condition"]["value"] == 100.0
        assert len(result["warnings"]) >= 1

        # Must still produce valid engineering_result
        validator = Draft202012Validator(engineering_schema)
        errors = list(validator.iter_errors(result["engineering_result"]))
        assert len(errors) == 0

    def test_insufficient_visual_evidence_warning(self) -> None:
        result = analyze_heritage_structure(vision_data=None)
        warnings_str = " ".join(result["warnings"]).lower()
        assert "no vision input" in warnings_str or "baseline" in warnings_str

    def test_auto_inference_of_unspecified_material(self) -> None:
        result = analyze_heritage_structure(structure_type="baoli", inferred_material=None)
        # Material should auto-infer to hydraulic_lime_mortar with warning
        assert result["material"]["original_material"] == "hydraulic_lime_mortar"
        assert result["material"]["verification_required"] is True
        warnings_str = " ".join(result["warnings"]).lower()
        assert "inferred" in warnings_str or "laboratory verification" in warnings_str

    def test_material_confidence_always_capped(self) -> None:
        result = analyze_heritage_structure(
            inferred_material="historic_sandstone",
            material_confidence=0.99
        )
        assert result["material"]["original_material_confidence"] <= 0.85
        assert result["material"]["verification_required"] is True
        assert len(result["material"]["recommended_tests"]) >= 3


class TestBackendIntegrationPayloadAssembly:
    """Verify that Swastik's backend can directly assemble a valid analysis.schema.json payload."""

    def test_assembly_of_analysis_contract(self, analysis_schema: dict) -> None:
        vision_mock = {
            "structure_type": "baoli",
            "image_dimensions": {"width_pixels": 1280, "height_pixels": 720},
            "detections": [
                {
                    "class_name": "crack",
                    "confidence": 0.85,
                    "bounding_box": [50.0, 100.0, 250.0, 300.0],
                    "pixel_area": 8500.0,
                    "coverage_ratio": 0.05,
                    "component_count": 1,
                    "relative_severity": "low",
                }
            ],
        }

        # Kirti's module computes everything
        eng_output = analyze_heritage_structure(
            structure_type="baoli",
            vision_data=vision_mock,
            inspection_data={"inlet_condition": "clear", "siltation_level": "low"},
        )

        # Swastik's backend assembles the final response
        full_analysis_payload = {
            "project_version": "0.1.0",
            "structure": {
                "type": "baoli",
                "name": "Agrasen ki Baoli",
                "region": "Delhi NCR",
                "source_images": ["https://jaldrishti.org/images/agrasen_01.jpg"],
            },
            "vision": vision_mock,
            "visual_condition": eng_output["engineering_result"]["visual_condition_score"],
            "water_functionality": eng_output["engineering_result"]["water_functionality_score"],
            "material": eng_output["material"],
            "root_cause": {"findings": eng_output["root_cause"]},
            "restoration": eng_output["restoration"],
            "metadata": {
                "created_at": "2026-10-08T12:00:00Z",
                "pipeline_status": "completed",
                "orchestrated_by": "FastAPI Orchestrator / Swastik Parmar",
            },
        }

        # Validate against contracts/analysis.schema.json
        validator = Draft202012Validator(analysis_schema)
        errors = list(validator.iter_errors(full_analysis_payload))
        assert len(errors) == 0, f"Analysis contract errors: {[e.message for e in errors]}"
