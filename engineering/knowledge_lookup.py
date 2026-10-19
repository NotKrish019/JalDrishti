"""Knowledge lookup service for traditional Indian water structures and IKS principles.

Provides deterministic, schema-validated access to the knowledge repository
for backend orchestration and frontend consumption.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from jsonschema import Draft202012Validator


class KnowledgeLookupError(Exception):
    """Base exception for knowledge lookup failures."""
    pass


class KnowledgeRepository:
    """Deterministic loader and query provider for IKS water structure knowledge."""

    def __init__(self, knowledge_root: Optional[Path] = None) -> None:
        if knowledge_root is None:
            # Default to repo root / knowledge
            knowledge_root = Path(__file__).resolve().parent.parent / "knowledge"
        self.root = knowledge_root
        self.structures_dir = self.root / "structures"
        self.sources_dir = self.root / "sources"
        self.iks_dir = self.root / "iks"

        self._structure_schema: Optional[Dict[str, Any]] = None
        self._sources_schema: Optional[Dict[str, Any]] = None
        self._sources_cache: Optional[List[Dict[str, Any]]] = None
        self._structures_cache: Dict[str, Dict[str, Any]] = {}

    def get_structure_schema(self) -> Dict[str, Any]:
        """Load and cache the structure JSON schema."""
        if self._structure_schema is None:
            schema_path = self.structures_dir / "structure.schema.json"
            if not schema_path.exists():
                raise KnowledgeLookupError(f"Structure schema not found at {schema_path}")
            with open(schema_path, "r", encoding="utf-8") as f:
                self._structure_schema = json.load(f)
        return self._structure_schema

    def get_sources_schema(self) -> Dict[str, Any]:
        """Load and cache the sources JSON schema."""
        if self._sources_schema is None:
            schema_path = self.sources_dir / "sources.schema.json"
            if not schema_path.exists():
                raise KnowledgeLookupError(f"Sources schema not found at {schema_path}")
            with open(schema_path, "r", encoding="utf-8") as f:
                self._sources_schema = json.load(f)
        return self._sources_schema

    def list_sources(self) -> List[Dict[str, Any]]:
        """Retrieve all documented research and literature sources."""
        if self._sources_cache is None:
            sources_path = self.sources_dir / "sources_index.json"
            if not sources_path.exists():
                raise KnowledgeLookupError(f"Sources index not found at {sources_path}")
            with open(sources_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            validator = Draft202012Validator(self.get_sources_schema())
            validator.validate(data)
            self._sources_cache = data
        return self._sources_cache

    def get_source_by_id(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Find a source record by its unique source_id."""
        sources = self.list_sources()
        for src in sources:
            if src.get("source_id") == source_id:
                return src
        return None

    def list_structure_ids(self) -> List[str]:
        """Return the IDs of all supported water structure typologies."""
        index_path = self.structures_dir / "index.json"
        if index_path.exists():
            with open(index_path, "r", encoding="utf-8") as f:
                index_data = json.load(f)
            return [s["id"] for s in index_data.get("structures", [])]

        return [f.stem for f in self.structures_dir.glob("*.json") if not f.name.endswith(".schema.json") and f.name != "index.json"]

    def get_structure(self, structure_id: str) -> Dict[str, Any]:
        """Load, validate, and return the knowledge entry for a given structure."""
        normalized_id = structure_id.strip().lower()
        if normalized_id in self._structures_cache:
            return self._structures_cache[normalized_id]

        file_path = self.structures_dir / f"{normalized_id}.json"
        if not file_path.exists():
            raise KnowledgeLookupError(
                f"Structure typology '{structure_id}' not found. Supported typologies: {self.list_structure_ids()}"
            )

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate against schema
        validator = Draft202012Validator(self.get_structure_schema())
        validator.validate(data)

        self._structures_cache[normalized_id] = data
        return data

    def list_all_structures(self) -> List[Dict[str, Any]]:
        """Return full data for all supported structures."""
        return [self.get_structure(sid) for sid in self.list_structure_ids()]

    def get_iks_principles(self) -> List[Dict[str, Any]]:
        """Retrieve formal IKS hydrological principles."""
        principles_path = self.iks_dir / "hydrology_principles.json"
        if not principles_path.exists():
            return []
        with open(principles_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("principles", [])

    def get_sources_by_evidence_type(self, evidence_type: str) -> List[Dict[str, Any]]:
        """Filter sources by evidence category (e.g. 'documented_historical_practice', 'modern_conservation_guidance')."""
        return [s for s in self.list_sources() if s.get("evidence_type") == evidence_type]

    def get_sources_by_structure_type(self, structure_type: str) -> List[Dict[str, Any]]:
        """Filter sources applicable to a specific structure typology."""
        norm_type = structure_type.strip().lower()
        return [
            s for s in self.list_sources()
            if norm_type in [t.lower() for t in s.get("applicable_structure_types", [])]
        ]

    def validate_knowledge_base(self) -> Dict[str, Any]:
        """Perform comprehensive consistency and schema verification."""
        results: Dict[str, Any] = {
            "sources_valid": False,
            "structures_valid": {},
            "hydrology_principles_valid": False,
            "unresolved_source_references": [],
            "status": "pending"
        }

        # Validate sources
        sources = self.list_sources()
        known_source_ids = {s["source_id"] for s in sources}
        results["sources_valid"] = len(sources) > 0

        # Validate structures
        for sid in self.list_structure_ids():
            try:
                struct_data = self.get_structure(sid)
                results["structures_valid"][sid] = True
                # Check for dangling source citations
                for src_ref in struct_data.get("sources", []):
                    if src_ref not in known_source_ids:
                        results["unresolved_source_references"].append((f"structure:{sid}", src_ref))
            except Exception as e:
                results["structures_valid"][sid] = str(e)

        # Validate IKS hydrology principles source references
        principles = self.get_iks_principles()
        if principles:
            for p in principles:
                p_code = p.get("code", "unknown")
                for s_ref in p.get("source_references", []):
                    if s_ref not in known_source_ids:
                        results["unresolved_source_references"].append((f"principle:{p_code}", s_ref))
            results["hydrology_principles_valid"] = True

        is_all_valid = (
            results["sources_valid"]
            and all(v is True for v in results["structures_valid"].values())
            and results["hydrology_principles_valid"]
            and len(results["unresolved_source_references"]) == 0
        )
        results["status"] = "passed" if is_all_valid else "failed"
        return results


# Module-level singleton instance for convenience
default_repository = KnowledgeRepository()


def get_structure(structure_id: str) -> Dict[str, Any]:
    """Convenience getter for structure knowledge."""
    return default_repository.get_structure(structure_id)


def list_structures() -> List[Dict[str, Any]]:
    """Convenience list of all structure knowledge entries."""
    return default_repository.list_all_structures()


def get_source(source_id: str) -> Optional[Dict[str, Any]]:
    """Convenience getter for research source by ID."""
    return default_repository.get_source_by_id(source_id)
