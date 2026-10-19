"""Unit and contract validation tests for Material DNA and Material Compatibility Engine (Phase 2).

Owner: Kirti Antil (IKS / Material Compatibility / Conservation Engineering Lead)
"""

import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator

from engineering.material_compatibility import (
    COMPATIBILITY_WEIGHTS,
    MaterialCompatibilityEngine,
    MaterialCompatibilityError,
    evaluate_compatibility,
)


WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
MATERIALS_DIR = WORKSPACE_ROOT / "knowledge" / "materials"
SOURCES_DIR = WORKSPACE_ROOT / "knowledge" / "sources"
CONTRACT_PATH = WORKSPACE_ROOT / "contracts" / "material_compatibility.schema.json"

EXPECTED_MATERIALS = [
    "hydraulic_lime_mortar",
    "surkhi_lime_mortar",
    "fat_lime_putty",
    "natural_hydraulic_lime_nhl",
    "historic_sandstone",
    "historic_quartzite",
    "lakhori_brick",
    "portland_cement_opc",
    "generic_acrylic_filler",
]


@pytest.fixture(scope="module")
def material_schema() -> dict:
    schema_file = MATERIALS_DIR / "material.schema.json"
    with open(schema_file, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def contract_schema() -> dict:
    with open(CONTRACT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def valid_source_ids() -> set:
    with open(SOURCES_DIR / "sources_index.json", "r", encoding="utf-8") as f:
        sources = json.load(f)
    return {s["source_id"] for s in sources}


class TestMaterialDNAProfiles:
    """Validate material JSON schemas, provenance, and data integrity."""

    def test_material_schema_is_valid_draft202012(self, material_schema: dict) -> None:
        Draft202012Validator.check_schema(material_schema)
        assert material_schema.get("$id") == "https://baoliguard.org/schemas/material.schema.json"

    @pytest.mark.parametrize("mat_id", EXPECTED_MATERIALS)
    def test_material_file_exists_and_conforms_to_schema(self, mat_id: str, material_schema: dict) -> None:
        file_path = MATERIALS_DIR / f"{mat_id}.json"
        assert file_path.exists(), f"Missing material profile file {file_path}"
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        validator = Draft202012Validator(material_schema)
        errors = list(validator.iter_errors(data))
        assert len(errors) == 0, f"Schema errors in {mat_id}: {[e.message for e in errors]}"

    @pytest.mark.parametrize("mat_id", EXPECTED_MATERIALS)
    def test_material_source_citations_resolve(self, mat_id: str, valid_source_ids: set) -> None:
        file_path = MATERIALS_DIR / f"{mat_id}.json"
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for src_ref in data.get("source_references", []):
            assert src_ref in valid_source_ids, f"Material '{mat_id}' references unknown source '{src_ref}'"

    def test_materials_index_completeness(self) -> None:
        index_file = MATERIALS_DIR / "index.json"
        assert index_file.exists()
        with open(index_file, "r", encoding="utf-8") as f:
            index_data = json.load(f)

        indexed_ids = {m["material_id"] for m in index_data.get("materials", [])}
        for mat_id in EXPECTED_MATERIALS:
            assert mat_id in indexed_ids, f"Material {mat_id} missing from materials index"


class TestMaterialCompatibilityEngineContract:
    """Validate that the engine generates payloads conforming strictly to contracts/material_compatibility.schema.json."""

    def test_compatibility_weights_sum_to_one(self) -> None:
        total = sum(COMPATIBILITY_WEIGHTS.values())
        assert abs(total - 1.0) < 1e-6, f"Weights must sum to 1.0, got {total}"

    def test_evaluate_lime_substrate_conforms_to_contract_schema(self, contract_schema: dict) -> None:
        engine = MaterialCompatibilityEngine(MATERIALS_DIR, CONTRACT_PATH)
        result = engine.evaluate(
            original_material="hydraulic_lime_mortar",
            original_material_confidence=0.80
        )

        validator = Draft202012Validator(contract_schema)
        errors = list(validator.iter_errors(result))
        assert len(errors) == 0, f"Contract validation errors: {[e.message for e in errors]}"
        assert result["verification_required"] is True
        assert len(result["recommended_tests"]) >= 3
        assert len(result["candidate_interventions"]) >= 4

    def test_evaluate_sandstone_substrate_conforms_to_contract_schema(self, contract_schema: dict) -> None:
        result = evaluate_compatibility(
            original_material="historic_sandstone",
            original_material_confidence=0.70
        )
        validator = Draft202012Validator(contract_schema)
        errors = list(validator.iter_errors(result))
        assert len(errors) == 0, f"Contract validation errors: {[e.message for e in errors]}"

    def test_confidence_is_capped_at_scientific_threshold(self) -> None:
        """Enforce rule: photo-identification cannot certify 100% certainty; must be capped <= 0.85."""
        engine = MaterialCompatibilityEngine(MATERIALS_DIR, CONTRACT_PATH)
        result = engine.evaluate("historic_sandstone", original_material_confidence=0.99)
        assert result["original_material_confidence"] <= 0.85
        assert result["verification_required"] is True


@pytest.fixture(scope="module")
def lime_evaluation() -> dict:
    return evaluate_compatibility("hydraulic_lime_mortar")


class TestMaterialCompatibilityDeterministicLogic:
    """Validate deterministic conservation engineering scoring and contextual reasoning."""

    def test_surkhi_mortar_is_strongly_recommended_on_lime(self, lime_evaluation: dict) -> None:
        surkhi = next(c for c in lime_evaluation["candidate_interventions"] if c["intervention_material"] == "surkhi_lime_mortar")
        assert surkhi["compatibility_score"] >= 80.0
        assert surkhi["recommendation"] == "strongly_recommended"
        assert surkhi["compatibility_dimensions"]["moisture"] >= 9.0
        assert surkhi["compatibility_dimensions"]["reversibility"] >= 8.5

    def test_portland_cement_is_prohibited_on_lime_with_reasons(self, lime_evaluation: dict) -> None:
        opc = next(c for c in lime_evaluation["candidate_interventions"] if c["intervention_material"] == "portland_cement_opc")
        assert opc["compatibility_score"] < 45.0
        assert opc["recommendation"] == "prohibited_incompatible"

        # Verify contextual reasoning in warnings (never simply 'no')
        warnings_text = " ".join(opc["warnings"])
        assert "moisture" in warnings_text.lower() or "vapor" in warnings_text.lower()
        assert "spalling" in warnings_text.lower() or "cryptoflorescence" in warnings_text.lower()
        assert "ettringite" in warnings_text.lower() or "sulfate" in warnings_text.lower()

    def test_acrylic_filler_is_prohibited_with_reversibility_warning(self, lime_evaluation: dict) -> None:
        acrylic = next(c for c in lime_evaluation["candidate_interventions"] if c["intervention_material"] == "generic_acrylic_filler")
        assert acrylic["compatibility_score"] < 45.0
        assert acrylic["recommendation"] == "prohibited_incompatible"
        assert acrylic["compatibility_dimensions"]["reversibility"] <= 2.0
        warnings_text = " ".join(acrylic["warnings"])
        assert "reversible" in warnings_text.lower() or "barrier" in warnings_text.lower()

    def test_nhl_mortar_is_recommended_or_acceptable(self, lime_evaluation: dict) -> None:
        nhl = next(c for c in lime_evaluation["candidate_interventions"] if c["intervention_material"] == "natural_hydraulic_lime_nhl")
        assert nhl["compatibility_score"] >= 65.0
        assert nhl["recommendation"] in ["recommended", "strongly_recommended"]

    def test_unknown_material_raises_descriptive_error(self) -> None:
        engine = MaterialCompatibilityEngine(MATERIALS_DIR, CONTRACT_PATH)
        with pytest.raises(MaterialCompatibilityError) as exc_info:
            engine.evaluate("alien_polymer_composite_2050")
        assert "not found" in str(exc_info.value)


class TestMissingAndConflictingMaterialData:
    """Validate graceful handling, warnings, and normalization for missing or conflicting data."""

    def test_missing_properties_triggers_warning_and_uses_baseline(self) -> None:
        engine = MaterialCompatibilityEngine(MATERIALS_DIR, CONTRACT_PATH)
        mock_incomplete_substrate = {
            "material_id": "incomplete_sandstone",
            "material_family": "stone",
            "category": "historic_substrate",
            "known_properties": {},  # completely missing strength and permeability
        }
        res = engine.evaluate_intervention(mock_incomplete_substrate, "surkhi_lime_mortar")
        warnings_str = " ".join(res["warnings"])
        assert "MISSING DATA" in warnings_str
        assert "compressive_strength_mpa_range" in warnings_str or "assumed" in warnings_str
        assert 0.0 <= res["compatibility_score"] <= 100.0

    def test_conflicting_inverted_bounds_normalized_with_warning(self) -> None:
        engine = MaterialCompatibilityEngine(MATERIALS_DIR, CONTRACT_PATH)
        mock_conflicting_substrate = {
            "material_id": "inverted_sandstone",
            "material_family": "stone",
            "category": "historic_substrate",
            "known_properties": {
                "compressive_strength_mpa_range": [25.0, 5.0],  # inverted: max < min
                "vapor_permeability_perm_range": [30.0, 10.0],
            },
        }
        res = engine.evaluate_intervention(mock_conflicting_substrate, "surkhi_lime_mortar")
        warnings_str = " ".join(res["warnings"])
        assert "CONFLICTING DATA" in warnings_str
        assert "inverted bounds" in warnings_str

    def test_negative_bounds_clamped_with_warning(self) -> None:
        engine = MaterialCompatibilityEngine(MATERIALS_DIR, CONTRACT_PATH)
        mock_negative_substrate = {
            "material_id": "negative_sandstone",
            "material_family": "stone",
            "category": "historic_substrate",
            "known_properties": {
                "compressive_strength_mpa_range": [-5.0, 8.0],
            },
        }
        res = engine.evaluate_intervention(mock_negative_substrate, "surkhi_lime_mortar")
        warnings_str = " ".join(res["warnings"])
        assert "CONFLICTING DATA" in warnings_str
        assert "negative values" in warnings_str


class TestExplainabilityAndDecisionSupport:
    """Validate rationales, provisional weight documentation, and safety caps."""

    def test_dimension_rationales_populated_for_all_dimensions(self, lime_evaluation: dict) -> None:
        surkhi = next(c for c in lime_evaluation["candidate_interventions"] if c["intervention_material"] == "surkhi_lime_mortar")
        assert "dimension_rationales" in surkhi
        rationales = surkhi["dimension_rationales"]
        required_dims = ["mechanical", "moisture", "thermal", "chemical", "reversibility", "heritage", "visual"]
        for dim in required_dims:
            assert dim in rationales
            assert len(rationales[dim].strip()) > 15, f"Rationale too brief for {dim}"

    def test_provisional_weights_and_screening_notice(self, lime_evaluation: dict) -> None:
        assert lime_evaluation.get("provisional_weights") is True
        assert "weight_validation_requirements" in lime_evaluation
        assert len(lime_evaluation["weight_validation_requirements"]) >= 2
        assert "evaluation_notice" in lime_evaluation
        assert "screening" in lime_evaluation["evaluation_notice"].lower()

    def test_low_confidence_substrate_triggers_safety_cap(self) -> None:
        """When substrate confidence is low (<0.60), recommendation must not be strongly_recommended."""
        engine = MaterialCompatibilityEngine(MATERIALS_DIR, CONTRACT_PATH)
        # Probabilistic identification is low (e.g. 0.40)
        result = engine.evaluate(
            original_material="hydraulic_lime_mortar",
            original_material_confidence=0.40
        )
        surkhi = next(c for c in result["candidate_interventions"] if c["intervention_material"] == "surkhi_lime_mortar")
        assert surkhi["recommendation"] == "acceptable_conditional"
        warnings_str = " ".join(surkhi["warnings"])
        assert "SAFETY CAP APPLIED" in warnings_str
        assert "acceptable_conditional" in warnings_str

