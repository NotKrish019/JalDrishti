"""Unit and contract validation tests for Indian Knowledge Systems (IKS) foundation (Phase 1).

Owner: Kirti Antil (IKS / Material Compatibility / Conservation Engineering Lead)
"""

import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator

from engineering.knowledge_lookup import KnowledgeRepository, default_repository


WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
KNOWLEDGE_ROOT = WORKSPACE_ROOT / "knowledge"
STRUCTURES_DIR = KNOWLEDGE_ROOT / "structures"
SOURCES_DIR = KNOWLEDGE_ROOT / "sources"
IKS_DIR = KNOWLEDGE_ROOT / "iks"

EXPECTED_STRUCTURES = ["baoli", "bawari", "kund", "vav"]


class TestIKSKnowledgeSchemas:
    """Validate JSON Schema definitions."""

    def test_structure_schema_is_valid_json_schema(self) -> None:
        schema_file = STRUCTURES_DIR / "structure.schema.json"
        assert schema_file.exists(), f"Missing schema at {schema_file}"
        with open(schema_file, "r", encoding="utf-8") as f:
            schema_data = json.load(f)
        Draft202012Validator.check_schema(schema_data)
        assert schema_data.get("$id") == "https://jaldrishti.org/schemas/structure.schema.json"

    def test_sources_schema_is_valid_json_schema(self) -> None:
        schema_file = SOURCES_DIR / "sources.schema.json"
        assert schema_file.exists(), f"Missing schema at {schema_file}"
        with open(schema_file, "r", encoding="utf-8") as f:
            schema_data = json.load(f)
        Draft202012Validator.check_schema(schema_data)


@pytest.fixture(scope="module")
def structure_schema() -> dict:
    schema_file = STRUCTURES_DIR / "structure.schema.json"
    with open(schema_file, "r", encoding="utf-8") as f:
        return json.load(f)


class TestIKSStructureEntries:
    """Validate structure knowledge content, engineering relevance, and schema compliance."""

    @pytest.mark.parametrize("struct_id", EXPECTED_STRUCTURES)
    def test_structure_file_exists(self, struct_id: str) -> None:
        struct_file = STRUCTURES_DIR / f"{struct_id}.json"
        assert struct_file.exists(), f"Missing structure file for {struct_id}"

    @pytest.mark.parametrize("struct_id", EXPECTED_STRUCTURES)
    def test_structure_schema_conformance(self, struct_id: str, structure_schema: dict) -> None:
        struct_file = STRUCTURES_DIR / f"{struct_id}.json"
        with open(struct_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        validator = Draft202012Validator(structure_schema)
        errors = list(validator.iter_errors(data))
        assert len(errors) == 0, f"Schema validation failed for {struct_id}: {[e.message for e in errors]}"

    @pytest.mark.parametrize("struct_id", EXPECTED_STRUCTURES)
    def test_engineering_relevance_fields(self, struct_id: str) -> None:
        """Ensure engineering principles explicitly define WHAT, WHY, HOW, and SIGNIFICANCE."""
        struct_file = STRUCTURES_DIR / f"{struct_id}.json"
        with open(struct_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        principles = data.get("engineering_principles", [])
        assert len(principles) >= 3, f"{struct_id} must have at least 3 detailed engineering principles"

        for p in principles:
            assert len(p["what"].strip()) > 10, f"Principle 'what' too brief in {struct_id}: {p['principle']}"
            assert len(p["why"].strip()) > 10, f"Principle 'why' too brief in {struct_id}: {p['principle']}"
            assert len(p["how"].strip()) > 10, f"Principle 'how' too brief in {struct_id}: {p['principle']}"
            assert len(p["engineering_significance"].strip()) > 10, (
                f"Principle 'engineering_significance' too brief in {struct_id}: {p['principle']}"
            )

    @pytest.mark.parametrize("struct_id", EXPECTED_STRUCTURES)
    def test_scientific_limitations_documented(self, struct_id: str) -> None:
        """Ensure every entry records scientific limitations and avoids unsupported certainty."""
        struct_file = STRUCTURES_DIR / f"{struct_id}.json"
        with open(struct_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        limitations = data.get("limitations", [])
        assert len(limitations) >= 2, f"{struct_id} must record explicit scientific limitations"


class TestResearchTraceability:
    """Validate citations and bibliographic provenance."""

    def test_sources_index_validity(self) -> None:
        schema_file = SOURCES_DIR / "sources.schema.json"
        index_file = SOURCES_DIR / "sources_index.json"

        with open(schema_file, "r", encoding="utf-8") as f:
            schema = json.load(f)
        with open(index_file, "r", encoding="utf-8") as f:
            sources = json.load(f)

        validator = Draft202012Validator(schema)
        errors = list(validator.iter_errors(sources))
        assert len(errors) == 0, f"Sources index schema error: {[e.message for e in errors]}"
        assert len(sources) >= 5, "At least 5 authoritative sources must be recorded"

    def test_all_structure_citations_resolve(self) -> None:
        """Verify that every citation in structure JSONs resolves to a valid source_id."""
        index_file = SOURCES_DIR / "sources_index.json"
        with open(index_file, "r", encoding="utf-8") as f:
            sources = json.load(f)
        valid_ids = {s["source_id"] for s in sources}

        for struct_id in EXPECTED_STRUCTURES:
            struct_file = STRUCTURES_DIR / f"{struct_id}.json"
            with open(struct_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for src in data.get("sources", []):
                assert src in valid_ids, f"Structure '{struct_id}' references unknown source '{src}'"


    def test_sources_rich_metadata_fields(self) -> None:
        """Verify that every source entry includes required academic and conservation fields."""
        index_file = SOURCES_DIR / "sources_index.json"
        with open(index_file, "r", encoding="utf-8") as f:
            sources = json.load(f)

        allowed_evidence_types = {
            "documented_historical_practice",
            "traditional_knowledge_recorded",
            "modern_conservation_guidance",
            "experimental_findings",
            "unverified_claim_hypothesis",
        }

        for src in sources:
            src_id = src["source_id"]
            assert "evidence_type" in src, f"{src_id} missing evidence_type"
            assert src["evidence_type"] in allowed_evidence_types, f"{src_id} has invalid evidence_type: {src['evidence_type']}"
            assert "relevant_region" in src and len(src["relevant_region"].strip()) > 5, f"{src_id} missing relevant_region"
            assert "confidence_limitations" in src and len(src["confidence_limitations"].strip()) > 10, f"{src_id} missing confidence_limitations"
            assert "practical_conservation_relevance" in src and len(src["practical_conservation_relevance"].strip()) > 10, f"{src_id} missing practical_conservation_relevance"
            assert "non_generalizable_conditions" in src and len(src["non_generalizable_conditions"]) >= 1, f"{src_id} missing non_generalizable_conditions"
            assert "applicable_structure_types" in src and len(src["applicable_structure_types"]) >= 1, f"{src_id} missing applicable_structure_types"
            assert src.get("expert_verification_status") in ["verified_authoritative", "provisional_guidance", "needs_field_validation"]

    def test_hydrology_principles_sources_resolve(self) -> None:
        """Verify that all source citations in hydrology_principles.json resolve to sources_index.json."""
        index_file = SOURCES_DIR / "sources_index.json"
        with open(index_file, "r", encoding="utf-8") as f:
            sources = json.load(f)
        valid_source_ids = {s["source_id"] for s in sources}

        principles = default_repository.get_iks_principles()
        for p in principles:
            p_code = p["code"]
            assert "source_references" in p and len(p["source_references"]) >= 1, f"Principle {p_code} missing source_references"
            for src_ref in p["source_references"]:
                assert src_ref in valid_source_ids, f"Principle {p_code} references unknown source '{src_ref}'"
            assert "limitations" in p and len(p["limitations"]) >= 1, f"Principle {p_code} missing limitations"


class TestKnowledgeLookupService:
    """Validate Python service layer for consumption by backend/frontend."""

    def test_repository_validation_passes(self) -> None:
        repo = KnowledgeRepository(KNOWLEDGE_ROOT)
        report = repo.validate_knowledge_base()
        assert report["status"] == "passed", f"Knowledge base validation failed: {report}"
        assert len(report["unresolved_source_references"]) == 0
        assert report["hydrology_principles_valid"] is True

    def test_get_individual_structures(self) -> None:
        for sid in EXPECTED_STRUCTURES:
            data = default_repository.get_structure(sid)
            assert data["id"] == sid
            assert len(data["traditional_materials"]) > 0

    def test_structure_not_found_raises(self) -> None:
        with pytest.raises(Exception):
            default_repository.get_structure("non_existent_typology")

    def test_iks_hydrology_principles_loaded(self) -> None:
        principles = default_repository.get_iks_principles()
        assert len(principles) >= 4, "Expected at least 4 formal IKS hydrological principles"
        codes = [p["code"] for p in principles]
        assert "IKS_HYDRO_01" in codes

    def test_filter_sources_by_evidence_type(self) -> None:
        guidance_sources = default_repository.get_sources_by_evidence_type("modern_conservation_guidance")
        assert len(guidance_sources) >= 2
        for s in guidance_sources:
            assert s["evidence_type"] == "modern_conservation_guidance"

    def test_filter_sources_by_structure_type(self) -> None:
        baoli_sources = default_repository.get_sources_by_structure_type("baoli")
        assert len(baoli_sources) >= 4
        for s in baoli_sources:
            assert "baoli" in [t.lower() for t in s.get("applicable_structure_types", [])]

    def test_missing_source_returns_none(self) -> None:
        assert default_repository.get_source_by_id("SRC_NONEXISTENT_9999") is None

