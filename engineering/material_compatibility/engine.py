"""Material Compatibility Engine for BaoliGuard heritage conservation.

Evaluates candidate intervention materials against historic substrates using deterministic,
multi-dimensional compatibility rules adhering strictly to
/contracts/material_compatibility.schema.json.

DISTINCTION MANDATE:
This engine generates a preliminary rule-based compatibility screening indicator.
It does NOT constitute a certified laboratory materials analysis or an autonomous
prescription for physical intervention. Laboratory characterization (petrography, XRD,
salt profiling) is mandatory prior to physical execution.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from jsonschema import Draft202012Validator

from engineering.material_compatibility.dimensions import (
    COMPATIBILITY_WEIGHTS,
    PROVISIONAL_COMPATIBILITY_WEIGHTS,
    WEIGHT_VALIDATION_REQUIREMENTS,
    RECOMMENDED_STANDARD_TESTS,
    evaluate_mechanical,
    evaluate_moisture,
    evaluate_thermal,
    evaluate_chemical,
    evaluate_reversibility,
    evaluate_heritage,
    evaluate_visual,
    compute_composite_compatibility,
)


class MaterialCompatibilityError(Exception):
    """Base exception for material compatibility failures."""
    pass


class MaterialCompatibilityEngine:
    """Deterministic, transparent decision-support engine for heritage material compatibility."""

    DEFAULT_CANDIDATES = [
        "surkhi_lime_mortar",
        "natural_hydraulic_lime_nhl",
        "fat_lime_putty",
        "portland_cement_opc",
        "generic_acrylic_filler",
    ]

    SCREENING_NOTICE = (
        "RULE-BASED SCREENING INDICATOR: This compatibility evaluation is a preliminary "
        "decision-support triage metric derived from published conservation literature and standardized "
        "material properties. It does NOT replace on-site petrographic, chemical, or XRD laboratory testing."
    )

    def __init__(self, materials_root: Optional[Path] = None, contract_path: Optional[Path] = None) -> None:
        if materials_root is None:
            materials_root = Path(__file__).resolve().parent.parent.parent / "knowledge" / "materials"
        if contract_path is None:
            contract_path = Path(__file__).resolve().parent.parent.parent / "contracts" / "material_compatibility.schema.json"

        self.materials_root = materials_root
        self.contract_path = contract_path
        self._profiles_cache: Dict[str, Dict[str, Any]] = {}
        self._schema_cache: Optional[Dict[str, Any]] = None

    def get_contract_schema(self) -> Dict[str, Any]:
        """Load and cache the contract JSON schema."""
        if self._schema_cache is None:
            if not self.contract_path.exists():
                raise MaterialCompatibilityError(f"Contract schema missing at {self.contract_path}")
            with open(self.contract_path, "r", encoding="utf-8") as f:
                self._schema_cache = json.load(f)
        return self._schema_cache

    def get_material_profile(self, material_id: str) -> Dict[str, Any]:
        """Load and cache a material DNA profile from JSON."""
        norm_id = material_id.strip().lower()
        # Aliases mapping for common names
        aliases = {
            "lime_mortar_hydraulic": "hydraulic_lime_mortar",
            "hydraulic_lime": "hydraulic_lime_mortar",
            "lime_mortar": "hydraulic_lime_mortar",
            "sandstone": "historic_sandstone",
            "sandstone_historic": "historic_sandstone",
            "sandstone_dholpur": "historic_sandstone",
            "sandstone_jodhpur": "historic_sandstone",
            "quartzite": "historic_quartzite",
            "quartzite_ashlar": "historic_quartzite",
            "delhi_quartzite": "historic_quartzite",
            "brick": "lakhori_brick",
            "lakhori": "lakhori_brick",
            "opc": "portland_cement_opc",
            "cement": "portland_cement_opc",
            "portland_cement": "portland_cement_opc",
            "acrylic": "generic_acrylic_filler",
            "epoxy": "generic_acrylic_filler",
            "surkhi": "surkhi_lime_mortar",
            "nhl": "natural_hydraulic_lime_nhl",
            "fat_lime": "fat_lime_putty",
        }
        canonical_id = aliases.get(norm_id, norm_id)

        if canonical_id in self._profiles_cache:
            return self._profiles_cache[canonical_id]

        file_path = self.materials_root / f"{canonical_id}.json"
        if not file_path.exists():
            raise MaterialCompatibilityError(
                f"Material DNA profile '{material_id}' (canonical '{canonical_id}') not found at {file_path}"
            )

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._profiles_cache[canonical_id] = data
        return data

    def list_available_materials(self) -> List[str]:
        """List all available material profile identifiers."""
        return [f.stem for f in self.materials_root.glob("*.json") if not f.name.endswith(".schema.json") and f.name != "index.json"]

    def evaluate_intervention(
        self,
        substrate_profile: Dict[str, Any],
        intervention_material_id: str,
        original_material_confidence: Optional[float] = None
    ) -> Dict[str, Any]:
        """Evaluate a single candidate intervention against a host substrate profile."""
        int_profile = self.get_material_profile(intervention_material_id)

        dim_scores: Dict[str, float] = {}
        dim_rationales: Dict[str, str] = {}
        all_warnings: List[str] = []

        # 1. Mechanical
        s_mech, w_mech, r_mech = evaluate_mechanical(substrate_profile, int_profile)
        dim_scores["mechanical"] = s_mech
        dim_rationales["mechanical"] = r_mech
        all_warnings.extend(w_mech)

        # 2. Moisture
        s_moist, w_moist, r_moist = evaluate_moisture(substrate_profile, int_profile)
        dim_scores["moisture"] = s_moist
        dim_rationales["moisture"] = r_moist
        all_warnings.extend(w_moist)

        # 3. Thermal
        s_therm, w_therm, r_therm = evaluate_thermal(substrate_profile, int_profile)
        dim_scores["thermal"] = s_therm
        dim_rationales["thermal"] = r_therm
        all_warnings.extend(w_therm)

        # 4. Chemical
        s_chem, w_chem, r_chem = evaluate_chemical(substrate_profile, int_profile)
        dim_scores["chemical"] = s_chem
        dim_rationales["chemical"] = r_chem
        all_warnings.extend(w_chem)

        # 5. Reversibility
        s_rev, w_rev, r_rev = evaluate_reversibility(int_profile)
        dim_scores["reversibility"] = s_rev
        dim_rationales["reversibility"] = r_rev
        all_warnings.extend(w_rev)

        # 6. Heritage
        s_heri, w_heri, r_heri = evaluate_heritage(substrate_profile, int_profile)
        dim_scores["heritage"] = s_heri
        dim_rationales["heritage"] = r_heri
        all_warnings.extend(w_heri)

        # 7. Visual
        s_vis, w_vis, r_vis = evaluate_visual(substrate_profile, int_profile)
        dim_scores["visual"] = s_vis
        dim_rationales["visual"] = r_vis
        all_warnings.extend(w_vis)

        # Composite score and recommendation (incorporating substrate identification confidence)
        composite_score, recommendation, advisories = compute_composite_compatibility(
            dim_scores,
            original_material_confidence=original_material_confidence
        )
        all_warnings.extend(advisories)

        return {
            "intervention_material": intervention_material_id,
            "compatibility_score": composite_score,
            "compatibility_dimensions": dim_scores,
            "recommendation": recommendation,
            "warnings": all_warnings,
            "dimension_rationales": dim_rationales,
        }

    def evaluate(
        self,
        original_material: str,
        candidate_materials: Optional[List[str]] = None,
        original_material_confidence: Optional[float] = None
    ) -> Dict[str, Any]:
        """Perform full multi-dimensional compatibility assessment conforming to contract.

        Args:
            original_material: Identified or inferred substrate (e.g. 'hydraulic_lime_mortar', 'historic_sandstone')
            candidate_materials: List of candidate repair materials to evaluate (defaults to standard set)
            original_material_confidence: Inferred confidence (0.0 to 1.0; capped at 0.85 to enforce probabilistic limit)

        Returns:
            Dict conforming strictly to /contracts/material_compatibility.schema.json
        """
        # Load substrate profile
        sub_profile = self.get_material_profile(original_material)

        # Scientific limit: photo-identification is probabilistic; cap confidence at 0.85
        if original_material_confidence is None:
            confidence = 0.75
        else:
            confidence = min(0.85, max(0.0, float(original_material_confidence)))

        if candidate_materials is None or len(candidate_materials) == 0:
            candidate_materials = list(self.DEFAULT_CANDIDATES)

        evaluations: List[Dict[str, Any]] = []
        for cand_id in candidate_materials:
            eval_res = self.evaluate_intervention(
                sub_profile,
                cand_id,
                original_material_confidence=confidence
            )
            evaluations.append(eval_res)

        payload: Dict[str, Any] = {
            "original_material": original_material,
            "original_material_confidence": confidence,
            "verification_required": True,
            "recommended_tests": list(RECOMMENDED_STANDARD_TESTS),
            "candidate_interventions": evaluations,
            "evaluation_notice": self.SCREENING_NOTICE,
            "provisional_weights": True,
            "weight_validation_requirements": list(WEIGHT_VALIDATION_REQUIREMENTS),
        }

        # Contract Schema Verification
        validator = Draft202012Validator(self.get_contract_schema())
        validator.validate(payload)

        return payload


default_engine = MaterialCompatibilityEngine()


def evaluate_compatibility(
    original_material: str,
    candidate_materials: Optional[List[str]] = None,
    original_material_confidence: Optional[float] = None
) -> Dict[str, Any]:
    """Convenience functional interface for material compatibility evaluation."""
    return default_engine.evaluate(
        original_material=original_material,
        candidate_materials=candidate_materials,
        original_material_confidence=original_material_confidence
    )
