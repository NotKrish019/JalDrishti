"""Conservation Restoration Planning and Priority Engine for BaoliGuard.

Generates phased, prioritized conservation roadmaps adhering to
/contracts/restoration_result.schema.json and /contracts/engineering_result.schema.json.
Integrates IKS traditional material specifications with modern conservation ethics.

CONSERVATION PRINCIPLE:
This planner is a decision-support tool. It organizes interventions into safe, sequenced
phases (Phase 1 Immediate Stabilization -> Phase 2 Hydrological Remediation ->
Phase 3 Masonry Consolidation -> Phase 4 Long-Term Monitoring) and enforces mandatory
expert engineering review before any physical structural intervention.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from jsonschema import Draft202012Validator


class RestorationPlanningEngine:
    """Constructs prioritized, phased conservation roadmaps based on diagnosis and material compatibility."""

    def __init__(self, contract_path: Optional[Path] = None) -> None:
        if contract_path is None:
            contract_path = Path(__file__).resolve().parent.parent.parent / "contracts" / "restoration_result.schema.json"
        self.contract_path = contract_path
        self._schema_cache: Optional[Dict[str, Any]] = None

    def get_contract_schema(self) -> Dict[str, Any]:
        """Load and cache the restoration result JSON schema."""
        if self._schema_cache is None:
            with open(self.contract_path, "r", encoding="utf-8") as f:
                self._schema_cache = json.load(f)
        return self._schema_cache

    def calculate_priority_score(
        self,
        visual_condition_score: float,
        water_functionality_score: float,
        root_causes: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Compute composite restoration priority score (0.0 = low priority, 100.0 = critical urgent emergency)."""
        # Urgency factor from root cause findings
        has_critical = any(rc.get("urgency") == "critical" for rc in root_causes)
        has_high = any(rc.get("urgency") == "high" for rc in root_causes)

        if has_critical:
            urgency_points = 95.0
        elif has_high:
            urgency_points = 75.0
        else:
            urgency_points = 40.0

        # Weighted calculation: degradation urgency (40%) + hydrological revival need (35%) + structural risk (25%)
        vis_urgency = max(0.0, 100.0 - visual_condition_score)
        hydro_urgency = max(0.0, 100.0 - water_functionality_score)

        composite_priority = round(
            (vis_urgency * 0.40) + (hydro_urgency * 0.35) + (urgency_points * 0.25),
            1
        )
        composite_priority = min(100.0, max(0.0, composite_priority))

        return {
            "value": composite_priority,
            "scale_min": 0.0,
            "scale_max": 100.0,
            "method": "weighted_multicriteria_restoration_urgency_v1",
            "confidence": 0.85,
            "limitations": [
                "Priority score is a decision-support heuristic combining visual degradation, hydraulic impairment, and qualitative root causes.",
                "Public safety hazards, seismic micro-zonation, and legal monument status must be factored into municipal work scheduling.",
                "Mandatory expert structural inspection required prior to allocating restoration capital budgets."
            ],
        }

    def determine_strategy(
        self,
        visual_condition_score: float,
        water_functionality_score: float,
    ) -> str:
        """Classify overall restoration strategy."""
        if visual_condition_score < 40.0 and water_functionality_score < 40.0:
            return "comprehensive_heritage_rehabilitation"
        elif water_functionality_score < 50.0:
            return "hydrological_revival"
        elif visual_condition_score < 60.0:
            return "material_consolidation"
        else:
            return "minimal_stabilization"

    def plan_restoration(
        self,
        structure_type: str = "baoli",
        visual_condition_score: float = 75.0,
        water_functionality_score: float = 60.0,
        crack_burden: float = 0.0,
        vegetation_burden: float = 0.0,
        spalling_burden: float = 0.0,
        dislodgement_burden: float = 0.0,
        siltation_level: str = "unknown",
        inlet_condition: str = "unknown",
        inferred_material: str = "hydraulic_lime_mortar",
        root_causes: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Construct full restoration result payload conforming strictly to restoration_result.schema.json."""
        if root_causes is None:
            root_causes = []

        strategy = self.determine_strategy(visual_condition_score, water_functionality_score)

        actions: List[Dict[str, Any]] = []
        step_counter = 1

        # PHASE 1: Immediate Stabilization
        if vegetation_burden > 0.05 or dislodgement_burden > 0.05:
            actions.append({
                "step": step_counter,
                "phase": "phase_1_immediate_stabilization",
                "action_title": "Gentle Bio-Enzymatic and Mechanical Root Extraction",
                "target_defect": "Invasive woody vegetation (Ficus / Prosopis) in stone bedding joints",
                "recommended_technique": (
                    "Excise stem at joint face; inject bio-safe ammonium sulfamate or localized vinegar solution into cambium "
                    "layer to devitalize deep root network without prying out surrounding stone masonry."
                ),
                "material_specification": "Eco-friendly root devitalizing agent; temporary dry timber wedges",
                "urgency": "immediate" if vegetation_burden > 0.15 else "high",
                "preconditions": [
                    "Install perimeter safety barricading around unstable descending stair flights.",
                    "Review by qualified heritage conservator required before cutting roots exceeding 80mm trunk diameter."
                ],
            })
            step_counter += 1

        if dislodgement_burden > 0.05 or crack_burden > 0.15:
            actions.append({
                "step": step_counter,
                "phase": "phase_1_immediate_stabilization",
                "action_title": "Temporary Shoring and Void Stabilization",
                "target_defect": "Tilted stone retaining revetment blocks and wide fracture gaps",
                "recommended_technique": (
                    "Install adjustable non-staining timber shores and hydraulic tell-tale displacement sensors across active "
                    "fracture apertures before commencing any dewatering or excavations."
                ),
                "material_specification": "Treated structural timber props, neoprene interface pads, crack displacement calipers",
                "urgency": "immediate",
                "preconditions": [
                    "Mandatory structural engineering on-site audit before permitting worker access into deep trench corridors.",
                    "Tell-tale monitoring must be established to verify crack movement dormancy."
                ],
            })
            step_counter += 1

        # PHASE 2: Hydrological Remediation
        if inlet_condition in ["choked", "broken", "partially_blocked"]:
            actions.append({
                "step": step_counter,
                "phase": "phase_2_hydrological_remediation",
                "action_title": "Catchment Feeder Channel Clearance & Silt Trap Restoration",
                "target_defect": "Choked runoff intake conduits and blocked peripheral settling sumps",
                "recommended_technique": (
                    "Manual clearing of debris from stone feeder channels (aagore); reinstate carved stone grating and "
                    "gravity sediment settling pits to clarify inflow before it spills into the main reservoir."
                ),
                "material_specification": "Dressed local sandstone baffle slabs; clean washed gravel filter bedding",
                "urgency": "high",
                "preconditions": [
                    "Complete Phase 1 immediate root and loose block stabilization.",
                    "Verify non-contamination of upstream catchment runoff."
                ],
            })
            step_counter += 1

        if siltation_level in ["severe", "moderate", "unknown"]:
            actions.append({
                "step": step_counter,
                "phase": "phase_2_hydrological_remediation",
                "action_title": "Manual Stratified Desiltation of Well Cylinder Bed",
                "target_defect": "Compacted impervious silt blanket sealing unconfined aquifer interface",
                "recommended_technique": (
                    "Manual de-silting using buckets and soft hand spades down to original stone slab or unmortared bedrock floor. "
                    "Strict prohibition of heavy hydraulic excavators inside historic well cylinders."
                ),
                "material_specification": "Manual hoist rigging, soft rubber spades, geotechnical silt disposal containers",
                "urgency": "high" if siltation_level == "severe" else "medium",
                "preconditions": [
                    "Geotechnical stability audit of well cylinder retaining walls before dewatering.",
                    "Verify groundwater table depth and secure lateral shoring props."
                ],
            })
            step_counter += 1

        # PHASE 3: Masonry & IKS Consolidation
        actions.append({
            "step": step_counter,
            "phase": "phase_3_masonry_and_iks_consolidation",
            "action_title": "Breathable Hydraulic Lime-Surkhi Repointing",
            "target_defect": "Eroded, washed-out, or cement-contaminated masonry bedding joints",
            "recommended_technique": (
                "Rake decayed joint mortar to a depth of twice the joint width using non-impact manual rakes. Flush with clean "
                "water and repoint with authentic slaked lime-surkhi pozzolanic mortar, compacting in 10mm layers."
            ),
            "material_specification": (
                "1 part slaked fat lime (Class C aged >6 months) : 2 parts calcined clay surkhi (IS 1344) : 1 part washed river sand, "
                "tempered with fermented jaggery (gur) and urad dal paste."
            ),
            "urgency": "medium",
            "preconditions": [
                "Desiltation complete; substrate cleared of debris and pre-wetted.",
                "Laboratory characterization of original historic mortar completed to confirm aggregate grading."
            ],
        })
        step_counter += 1

        if spalling_burden > 0.05:
            actions.append({
                "step": step_counter,
                "phase": "phase_3_masonry_and_iks_consolidation",
                "action_title": "Desalination Poulticing and Stone Consolidation",
                "target_defect": "Salt crypto-efflorescence and surface sandstone blister spalling",
                "recommended_technique": (
                    "Apply demineralized water cellulose / sepiolite clay poultices to extract entrapped sub-surface nitrates and "
                    "sulfates. Micro-grout deep delaminated stone voids using ultra-fine natural hydraulic lime (NHL 2)."
                ),
                "material_specification": "Sepiolite clay pulp, demineralized water, NHL 2 micro-injection grout",
                "urgency": "medium",
                "preconditions": [
                    "Laboratory soluble salt ion chromatography completed to determine salt profile.",
                    "Eliminate external rising damp / drainage leak sources first."
                ],
            })
            step_counter += 1

        # PHASE 4: Long-Term Monitoring
        actions.append({
            "step": step_counter,
            "phase": "phase_4_long_term_monitoring",
            "action_title": "Seasonal Piezometer and Microcrack Displacement Monitoring",
            "target_defect": "Long-term cyclic hydrostatic load variations and environmental moisture equilibrium",
            "recommended_technique": (
                "Install calibrated tell-tale glass displacement gauges on structural arch joints. Log post-monsoon and "
                "pre-monsoon water level fluctuations using ultrasonic depth loggers."
            ),
            "material_specification": "Calibrated optical crack monitoring plates, piezometric groundwater data logger",
            "urgency": "routine",
            "preconditions": ["Phase 3 masonry consolidation successfully cured for minimum 28 days."],
        })

        # Explicit warnings against destructive modern practices
        incompatible_practices = [
            {
                "prohibited_action": "Application of Ordinary Portland Cement (OPC) pointing, plastering, or grouting.",
                "failure_mechanism": (
                    "OPC forms a non-breathable vapor barrier (<3 Perm) on breathable historic stone. Trapped subsurface moisture "
                    "forces salt crystallization behind the cement crust, inducing catastrophic cryptoflorescence and accelerated stone arrises spalling."
                ),
                "severity": "destructive",
            },
            {
                "prohibited_action": "Injection of synthetic acrylic resins, polyurethane foams, or epoxy crack fillers.",
                "failure_mechanism": (
                    "Irreversible synthetic adhesives have thermal expansion coefficients 4 to 8 times higher than historic sandstone, "
                    "inducing shear tearing of the host stone face under desert diurnal heat cycles."
                ),
                "severity": "destructive",
            },
            {
                "prohibited_action": "Use of heavy tracked mechanical excavators (JCBs) inside stepwell basins.",
                "failure_mechanism": (
                    "Vibratory impact and heavy point loads fracture historic submerged stone pavements, dislodge unreinforced step blocks, "
                    "and crack subterranean retaining wall basements."
                ),
                "severity": "high_risk",
            },
            {
                "prohibited_action": "Application of harsh synthetic chemical algaecides (copper sulfate / hydrochloric acid).",
                "failure_mechanism": (
                    "Acidic cleaners dissolve calcium carbonate binders in historic lime mortars and calcitic sandstones, causing permanent structural pitting."
                ),
                "severity": "high_risk",
            },
        ]

        # IKS Traditional Guidelines with explicit caveats
        iks_guidelines = {
            "traditional_mortar_recipe": (
                "Authentic Hydraulic Lime-Surkhi Mortar: 1 part slaked fat lime putty (Class C, cured >90 days) : "
                "2 parts finely pulverized calcined terracotta surkhi (particle size 0.15-2.0mm, IS 1344) : 1 part sieved river quartz sand. "
                "Slaked with 5% fermented jaggery (gur) decoction, 2% black gram paste (urad dal), and bael fruit pulp mucilage. "
                "CAVEAT: This recipe provides traditional regional guidance for northwestern sandstone structures. Proportions must "
                "be verified against petrographic testing of original mortar samples and adjusted for regional quarry sands."
            ),
            "craftsmanship_references": [
                "Shilpa Shastras & Manasara: Indigenous treatises on subterranean masonry joinery and hydraulic orientation.",
                "INTACH Charter (2004) Section 5: Traditional Craftsmanship and Living Heritage Stewardship.",
                "ASI Architectural Conservation Manual (2020): Traditional Lime Preparation and Slaking Protocols.",
                "CPWD Handbook of Conservation of Heritage Buildings (2013): Mortar Batching & Organic Additives.",
            ],
            "seasonal_curing_rules": (
                "Slow carbonation curing: Fresh lime joints must be protected from direct sunlight, freezing, and desiccating winds. "
                "Maintain continuous dampness using double-layer wet hessian/jute sacking for a minimum of 21 consecutive days. "
                "Never allow rapid air drying; do not apply during frost or when temperatures exceed 40°C. "
                "In deep unventilated subterranean shafts, monitor for fungal growth if organic herbal admixtures are used."
            ),
        }

        payload: Dict[str, Any] = {
            "restoration_strategy": strategy,
            "prioritized_actions": actions,
            "incompatible_practices": incompatible_practices,
            "iks_guidelines": iks_guidelines,
        }

        # Contract Schema Verification
        validator = Draft202012Validator(self.get_contract_schema())
        validator.validate(payload)

        return payload


default_restoration_engine = RestorationPlanningEngine()


def plan_restoration(
    structure_type: str = "baoli",
    visual_condition_score: float = 75.0,
    water_functionality_score: float = 60.0,
    crack_burden: float = 0.0,
    vegetation_burden: float = 0.0,
    spalling_burden: float = 0.0,
    dislodgement_burden: float = 0.0,
    siltation_level: str = "unknown",
    inlet_condition: str = "unknown",
    inferred_material: str = "hydraulic_lime_mortar",
    root_causes: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Convenience function for restoration planning."""
    return default_restoration_engine.plan_restoration(
        structure_type=structure_type,
        visual_condition_score=visual_condition_score,
        water_functionality_score=water_functionality_score,
        crack_burden=crack_burden,
        vegetation_burden=vegetation_burden,
        spalling_burden=spalling_burden,
        dislodgement_burden=dislodgement_burden,
        siltation_level=siltation_level,
        inlet_condition=inlet_condition,
        inferred_material=inferred_material,
        root_causes=root_causes,
    )
