"""Unified Conservation Engineering Service Facade.

Prepares the complete Kirti-owned engineering subsystem for integration with:
- Swastik's FastAPI backend (orchestration & schema validation)
- Anika's frontend (2D dashboards & 3D digital twin)

Provides robust input validation, missing-data handling, uncertain material
identification, and contract-conforming outputs.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union

from engineering.knowledge_lookup import (
    KnowledgeRepository,
    default_repository,
    get_structure,
    list_structures,
)
from engineering.material_compatibility import (
    COMPATIBILITY_WEIGHTS,
    MaterialCompatibilityEngine,
    default_engine as default_material_engine,
    evaluate_compatibility,
)
from engineering.scoring.visual_condition import (
    VisualConditionScorer,
    calculate_visual_condition,
    default_visual_scorer,
)
from engineering.water_functionality.water_scorer import (
    WaterFunctionalityScorer,
    calculate_water_functionality,
    default_water_scorer,
)
from engineering.root_cause.deduction_rules import (
    RootCauseDeductionEngine,
    deduce_root_causes,
    default_root_cause_engine,
)
from engineering.restoration.restoration_planner import (
    RestorationPlanningEngine,
    default_restoration_engine,
    plan_restoration,
)
from engineering.assessment import (
    DEFAULT_ENGINEERING_DISCLAIMER,
    EngineeringAssessmentEngine,
    default_assessment_engine,
    run_engineering_assessment,
)


logger = logging.getLogger("jaldrishti.engineering")


# Typology to default historic substrate inference mapping
TYPOLOGY_MATERIAL_DEFAULTS: Dict[str, str] = {
    "baoli": "hydraulic_lime_mortar",
    "bawari": "historic_sandstone",
    "kund": "historic_sandstone",
    "vav": "historic_sandstone",
    "tank": "hydraulic_lime_mortar",
    "unknown": "hydraulic_lime_mortar",
}


class ConservationEngineeringService:
    """Master facade coordinating all engineering and IKS subsystems with comprehensive error handling."""

    def __init__(self) -> None:
        self.knowledge_repo = default_repository
        self.material_engine = default_material_engine
        self.visual_scorer = default_visual_scorer
        self.water_scorer = default_water_scorer
        self.root_cause_engine = default_root_cause_engine
        self.restoration_engine = default_restoration_engine
        self.assessment_engine = default_assessment_engine

    def parse_vision_input(
        self,
        vision_input: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, float], float, List[str]]:
        """Parse and normalize vision subsystem inputs (from vision_result or raw detections)."""
        warnings: List[str] = []
        detections: List[Dict[str, Any]] = []

        if vision_input is None:
            warnings.append("No vision input provided; visual condition evaluated using conservative baseline defaults.")
            return detections, {"crack": 0.0, "vegetation": 0.0, "spalling": 0.0, "dislodgement": 0.0}, 0.50, warnings

        if isinstance(vision_input, dict):
            # Payload matching vision_result.schema.json
            detections = vision_input.get("detections", [])
            if not detections:
                warnings.append("Vision payload contained zero defect detections; assuming clear surface masonry.")
        elif isinstance(vision_input, list):
            detections = vision_input

        # Aggregate burdens
        burdens = {"crack": 0.0, "vegetation": 0.0, "spalling": 0.0, "dislodgement": 0.0}
        confidences: List[float] = []

        for d in detections:
            c_name = d.get("class_name", "").lower()
            cov = float(d.get("coverage_ratio", 0.0))
            conf = float(d.get("confidence", 0.75))
            confidences.append(conf)

            if "crack" in c_name:
                burdens["crack"] += cov
            elif "vegetation" in c_name or "root" in c_name:
                burdens["vegetation"] += cov
            elif "spall" in c_name:
                burdens["spalling"] += cov
            elif "dislodg" in c_name:
                burdens["dislodgement"] += cov

        # Cap burdens at 1.0
        for k in burdens:
            burdens[k] = min(1.0, burdens[k])

        avg_conf = round(sum(confidences) / len(confidences), 2) if confidences else 0.80
        return detections, burdens, avg_conf, warnings

    def analyze_structure(
        self,
        structure_type: Optional[str] = None,
        vision_data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
        inspection_data: Optional[Dict[str, Any]] = None,
        inferred_material: Optional[str] = None,
        material_confidence: Optional[float] = None,
        candidate_materials: Optional[List[str]] = None,
        recent_repair_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Perform end-to-end engineering assessment, material compatibility, and restoration planning.

        Args:
            structure_type: Heritage typology ('baoli', 'bawari', 'kund', 'vav', or None)
            vision_data: Output from vision subsystem (dict or list of detections)
            inspection_data: Hydrological parameters (inlet, outlet, siltation, catchment, water_presence)
            inferred_material: Inferred substrate material identifier
            material_confidence: Probabilistic confidence in material identification (capped at 0.85)
            candidate_materials: Specific candidate materials to evaluate
            recent_repair_type: Modern repair observed on site (e.g. 'portland_cement_opc')

        Returns:
            Unified dictionary ready for backend orchestration and frontend rendering.
        """
        all_warnings: List[str] = []
        all_limitations: List[str] = [
            DEFAULT_ENGINEERING_DISCLAIMER,
            "Photographic evidence cannot certify chemical binder composition; laboratory testing is mandatory.",
        ]

        # 1. Normalize Structure Type
        norm_type = (structure_type or "unknown").strip().lower()
        if norm_type not in ["baoli", "bawari", "kund", "vav", "tank", "unknown"]:
            all_warnings.append(f"Unrecognized structure typology '{structure_type}'; using generalized hydraulic rules.")
            norm_type = "unknown"

        # 2. Parse Vision Data
        detections, burdens, vision_conf, vision_warnings = self.parse_vision_input(vision_data)
        all_warnings.extend(vision_warnings)

        # 3. Parse Inspection Data
        insp = inspection_data or {}
        inlet = insp.get("inlet_condition", "unknown")
        outlet = insp.get("outlet_condition", "unknown")
        siltation = insp.get("siltation_level", "unknown")
        water = insp.get("water_presence", "unknown")
        catchment = insp.get("catchment_condition", "unknown")
        accessibility = insp.get("accessibility_status", insp.get("accessibility", "unknown"))

        # 4. Resolve Historic Material
        if not inferred_material:
            mat_id = TYPOLOGY_MATERIAL_DEFAULTS.get(norm_type, "hydraulic_lime_mortar")
            all_warnings.append(
                f"No original material specified. Inferred '{mat_id}' from typology '{norm_type}'. Laboratory verification required."
            )
        else:
            mat_id = inferred_material.strip().lower()

        # 5. Execute Sub-Engines
        # A. Visual Condition
        vis_res = self.visual_scorer.calculate_score(
            detections=detections,
            crack_burden=burdens["crack"],
            vegetation_burden=burdens["vegetation"],
            spalling_burden=burdens["spalling"],
            dislodgement_burden=burdens["dislodgement"],
            confidence_override=vision_conf,
        )
        visual_score = vis_res["visual_condition_score"]

        # B. Water Functionality
        water_res = self.water_scorer.calculate_score(
            inlet_condition=inlet,
            outlet_condition=outlet,
            siltation_level=siltation,
            water_presence=water,
            catchment_condition=catchment,
            accessibility=accessibility,
        )
        water_score = water_res["water_functionality_score"]

        # C. Root Cause Deductions
        root_causes = self.root_cause_engine.deduce(
            crack_burden=burdens["crack"],
            vegetation_burden=burdens["vegetation"],
            spalling_burden=burdens["spalling"],
            dislodgement_burden=burdens["dislodgement"],
            inlet_condition=inlet,
            outlet_condition=outlet,
            siltation_level=siltation,
            water_presence=water,
            catchment_condition=catchment,
            inferred_material=mat_id,
            recent_repair_type=recent_repair_type,
        )

        # D. Material Compatibility
        mat_res = self.material_engine.evaluate(
            original_material=mat_id,
            candidate_materials=candidate_materials,
            original_material_confidence=material_confidence,
        )

        # E. Restoration Planning & Priority
        resto_res = self.restoration_engine.plan_restoration(
            structure_type=norm_type,
            visual_condition_score=visual_score["value"],
            water_functionality_score=water_score["value"],
            crack_burden=burdens["crack"],
            vegetation_burden=burdens["vegetation"],
            spalling_burden=burdens["spalling"],
            dislodgement_burden=burdens["dislodgement"],
            siltation_level=siltation,
            inlet_condition=inlet,
            inferred_material=mat_id,
            root_causes=root_causes,
        )
        priority_metric = self.restoration_engine.calculate_priority_score(
            visual_condition_score=visual_score["value"],
            water_functionality_score=water_score["value"],
            root_causes=root_causes,
        )

        # Aggregate warnings from candidate evaluations
        for cand in mat_res.get("candidate_interventions", []):
            if cand.get("recommendation") == "prohibited_incompatible":
                all_warnings.extend(cand.get("warnings", []))

        # Assemble unified payload
        combined_sub_scores = {
            "vegetation_intrusion_index": vis_res["sub_scores"].get("vegetation_intrusion_index"),
            "masonry_integrity_index": vis_res["sub_scores"].get("masonry_integrity_index"),
            "siltation_obstruction_index": water_res["sub_scores"].get("siltation_obstruction_index"),
        }

        engineering_result_payload = {
            "visual_condition_score": visual_score,
            "water_functionality_score": water_score,
            "restoration_priority_score": priority_metric,
            "sub_scores": combined_sub_scores,
            "root_cause_analysis": root_causes,
            "engineering_disclaimer": DEFAULT_ENGINEERING_DISCLAIMER,
        }

        return {
            "structure_type": norm_type,
            "visual_condition": visual_score,
            "water_functionality": water_score,
            "material": mat_res,
            "root_cause": root_causes,
            "restoration": resto_res,
            "restoration_priority": priority_metric,
            "engineering_result": engineering_result_payload,
            "sub_scores": combined_sub_scores,
            "warnings": list(set(all_warnings)),
            "limitations": all_limitations,
        }


default_service = ConservationEngineeringService()


def analyze_heritage_structure(
    structure_type: Optional[str] = None,
    vision_data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
    inspection_data: Optional[Dict[str, Any]] = None,
    inferred_material: Optional[str] = None,
    material_confidence: Optional[float] = None,
    candidate_materials: Optional[List[str]] = None,
    recent_repair_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Convenience function providing complete heritage engineering analysis."""
    return default_service.analyze_structure(
        structure_type=structure_type,
        vision_data=vision_data,
        inspection_data=inspection_data,
        inferred_material=inferred_material,
        material_confidence=material_confidence,
        candidate_materials=candidate_materials,
        recent_repair_type=recent_repair_type,
    )
