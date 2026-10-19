"""Multi-dimensional material compatibility evaluation rules and scoring logic.

Evaluates candidate intervention materials against historic substrates across
7 transparent, deterministic conservation engineering dimensions:
1. Mechanical Compatibility (Sacrificial stiffness & strength; RILEM TC 203-RHM)
2. Moisture Compatibility (Breathability, vapor permeability & capillary behavior; IS 3115)
3. Thermal Compatibility (Thermal expansion coefficient matching under diurnal cycles)
4. Chemical Compatibility (Absence of soluble sulfates/alkalis, ettringite prevention)
5. Reversibility (Retreatability without host substrate destruction; INTACH Charter)
6. Heritage Alignment (Conformity to IKS traditions, ASI & INTACH conservation ethics)
7. Visual Compatibility (Texture, patina, color, and aggregate harmony)

PROVISIONAL WEIGHTS NOTICE:
The dimension weights defined below are PROVISIONAL SCREENING HEURISTICS synthesized
from conservation literature (RILEM TC 203-RHM, ASI Conservation Manual 2020, and
CPWD Guidelines). They provide a risk-ranked screening metric for preliminary
decision support and MUST NOT be construed as a substitute for certified laboratory
characterization (XRD, petrography, salt profiling).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


# Deterministic dimension weighting summing to 1.00 (100%)
# PROVISIONAL: Derived from conservation consensus literature.
COMPATIBILITY_WEIGHTS: Dict[str, float] = {
    "moisture": 0.25,      # Critical: moisture entrapment is the primary cause of subterranean masonry decay
    "mechanical": 0.20,    # Sacrificial principle: mortar must yield before historic stone arrises fracture
    "chemical": 0.15,      # Prevention of soluble salt crystallization, ettringite & thaumasite attack
    "reversibility": 0.15, # Core conservation mandate: non-destructive retreatability without host loss
    "heritage": 0.10,      # Preservation of authentic IKS formulations, materials, and craftsmanship
    "thermal": 0.10,       # Prevention of interfacial shearing under semi-arid diurnal temperature swings
    "visual": 0.05,        # Aesthetic patina, color harmony, and aggregate texture compatibility
}

# Alias explicitly indicating provisional status
PROVISIONAL_COMPATIBILITY_WEIGHTS = COMPATIBILITY_WEIGHTS

WEIGHT_VALIDATION_REQUIREMENTS: List[str] = [
    "Empirical shear-bond strength laboratory testing across regional sandstone and quartzite varieties.",
    "Cyclic salt-crystallization chamber durability testing for hydraulic lime-surkhi blends.",
    "Field calibration against long-term in-situ mortar performance in monitored ASI/INTACH pilot projects.",
]

RECOMMENDED_STANDARD_TESTS: List[str] = [
    "Thin-section petrographic microscopy for mineralogical aggregate classification",
    "X-ray powder diffraction (XRD) for binder crystalline phase characterization",
    "Acid digestion and gravimetric insoluble residue analysis for binder-to-aggregate ratio",
    "Standard RILEM tube water absorption test for capillary moisture uptake",
    "Soluble salt ion chromatography (sulfate, nitrate, chloride concentrations)",
]


def _extract_range(
    data: Dict[str, Any],
    prop_name: str,
    default_range: Tuple[float, float],
    warnings: List[str],
    entity_label: str
) -> Tuple[float, float]:
    """Helper to safely extract property ranges with missing and conflicting data detection."""
    known_props = data.get("known_properties", {})
    if not isinstance(known_props, dict):
        warnings.append(
            f"MISSING DATA: {entity_label} has no known_properties block; using screening baseline {default_range}."
        )
        return default_range

    raw_val = known_props.get(prop_name)
    if raw_val is None:
        warnings.append(
            f"MISSING DATA: '{prop_name}' missing for {entity_label}; assumed screening baseline {default_range}."
        )
        return default_range

    if not isinstance(raw_val, (list, tuple)) or len(raw_val) < 2:
        warnings.append(
            f"MALFORMED DATA: '{prop_name}' for {entity_label} is not a valid 2-element range; using default {default_range}."
        )
        return default_range

    try:
        val_min = float(raw_val[0])
        val_max = float(raw_val[1])
    except (ValueError, TypeError):
        warnings.append(
            f"NON-NUMERIC DATA: '{prop_name}' in {entity_label} contains non-numeric values; using default {default_range}."
        )
        return default_range

    if val_min > val_max:
        warnings.append(
            f"CONFLICTING DATA: '{prop_name}' in {entity_label} has inverted bounds [{val_min}, {val_max}]; normalized to [{val_max}, {val_min}]."
        )
        val_min, val_max = val_max, val_min

    if val_min < 0:
        warnings.append(
            f"CONFLICTING DATA: '{prop_name}' in {entity_label} contains negative values [{val_min}, {val_max}]; clamped to positive domain."
        )
        val_min = max(0.0, val_min)
        val_max = max(0.0, val_max)

    return val_min, val_max


def evaluate_mechanical(
    substrate: Dict[str, Any],
    intervention: Dict[str, Any]
) -> Tuple[float, List[str], str]:
    """Evaluate mechanical compatibility and sacrificial behavior.

    Conservation Rule: An intervention mortar must have lower stiffness (elastic modulus)
    and compressive strength than the host substrate, acting sacrificially to protect historic fabric.
    """
    warnings: List[str] = []
    sub_min, sub_max = _extract_range(
        substrate, "compressive_strength_mpa_range", (2.0, 5.0), warnings, "substrate"
    )
    int_min, int_max = _extract_range(
        intervention, "compressive_strength_mpa_range", (2.0, 5.0), warnings, "intervention"
    )

    sub_mid = (sub_min + sub_max) / 2.0
    int_mid = (int_min + int_max) / 2.0

    ratio = int_mid / max(sub_mid, 0.5)

    if ratio > 2.0:
        score = max(1.0, 10.0 - (ratio * 2.2))
        rationale = (
            f"Severe anti-sacrificial mechanical mismatch: Intervention compressive strength (~{int_mid:.1f} MPa) "
            f"exceeds substrate strength (~{sub_mid:.1f} MPa) by a factor of {ratio:.1f}x. Rigid mortar will "
            f"cause edge spalling of the softer historic stone under cyclic loading."
        )
        warnings.append(
            f"MECHANICAL MISMATCH: Intervention compressive strength (~{int_mid:.1f} MPa) significantly exceeds "
            f"substrate capacity (~{sub_mid:.1f} MPa). The repair is anti-sacrificial; thermal and ground movements "
            f"will force fractures through the historic stone/brick edges rather than yielding in the joint."
        )
    elif ratio > 1.2:
        score = 4.5
        rationale = (
            f"Elevated stiffness: Intervention compressive strength (~{int_mid:.1f} MPa) is moderately higher than "
            f"substrate capacity (~{sub_mid:.1f} MPa). Minor stress concentration risk at masonry contact interfaces."
        )
        warnings.append(
            f"ELEVATED STIFFNESS: Intervention strength (~{int_mid:.1f} MPa) exceeds substrate strength (~{sub_mid:.1f} MPa). "
            f"High risk of localized stress concentration and accelerated arrises spalling."
        )
    elif 0.4 <= ratio <= 1.2:
        # Ideal sacrificial range
        score = 9.5
        rationale = (
            f"Sacrificial compatibility confirmed: Intervention compressive strength (~{int_mid:.1f} MPa) is within "
            f"the optimal sacrificial ductile envelope (ratio: {ratio:.2f}) relative to substrate (~{sub_mid:.1f} MPa)."
        )
    elif 0.2 <= ratio < 0.4:
        score = 7.5
        rationale = (
            f"Soft ductile repair: Intervention strength (~{int_mid:.1f} MPa) is low relative to substrate "
            f"(~{sub_mid:.1f} MPa). Excellent sacrificial compliance; suitable for bedding, pointing, and non-load-bearing renders."
        )
    else:
        score = 5.0
        rationale = (
            f"Very low strength: Intervention (~{int_mid:.1f} MPa) possesses minimal compressive capacity. "
            f"Not suitable for structural load-bearing masonry without reinforcing pozzolanic additives."
        )
        warnings.append("VERY LOW STRENGTH: Suitable only for non-structural pointing and decorative renders.")

    return round(min(10.0, max(0.0, score)), 1), warnings, rationale


def evaluate_moisture(
    substrate: Dict[str, Any],
    intervention: Dict[str, Any]
) -> Tuple[float, List[str], str]:
    """Evaluate moisture compatibility and breathability.

    Conservation Rule: The intervention must remain more permeable or equally permeable
    to water vapor compared to the host masonry to prevent moisture entrapment.
    """
    warnings: List[str] = []
    sub_min, sub_max = _extract_range(
        substrate, "vapor_permeability_perm_range", (10.0, 20.0), warnings, "substrate"
    )
    int_min, int_max = _extract_range(
        intervention, "vapor_permeability_perm_range", (10.0, 20.0), warnings, "intervention"
    )

    sub_mid = (sub_min + sub_max) / 2.0
    int_mid = (int_min + int_max) / 2.0

    if int_mid < 3.0:
        # Severe vapor barrier (OPC or synthetic resin)
        score = 1.0
        rationale = (
            f"Critical moisture barrier: Intervention vapor permeability (~{int_mid:.1f} Perm) acts as an impermeable "
            f"skin over breathable historic substrate (~{sub_mid:.1f} Perm). Traps moisture and causes subsurface salt spalling."
        )
        warnings.append(
            f"CRITICAL MOISTURE BARRIER: Intervention vapor permeability (~{int_mid:.1f} Perm) acts as an impermeable "
            f"seal on breathable historic masonry (~{sub_mid:.1f} Perm). Subsurface rising damp will be forced sideways, "
            f"triggering cryptoflorescence, frost wedging, and destructive stone face spalling."
        )
    elif int_mid < sub_mid * 0.7:
        score = 4.0
        rationale = (
            f"Restricted breathability: Intervention vapor permeability (~{int_mid:.1f} Perm) is significantly lower than "
            f"substrate (~{sub_mid:.1f} Perm). Moisture drying rates will be impeded."
        )
        warnings.append(
            f"RESTRICTED BREATHABILITY: Permeability (~{int_mid:.1f} Perm) is lower than substrate (~{sub_mid:.1f} Perm). "
            f"Drying rate will be impeded, increasing risk of damp retention in masonry core."
        )
    elif int_mid >= sub_mid * 0.9:
        score = 9.8
        rationale = (
            f"Optimal hygric compatibility: High vapor permeability (~{int_mid:.1f} Perm) allows continuous moisture "
            f"evaporation, preventing damp accumulation behind joints."
        )
    else:
        score = 7.5
        rationale = (
            f"Acceptable moisture compatibility: Permeability (~{int_mid:.1f} Perm) matches the general breathable range "
            f"of historic masonry (~{sub_mid:.1f} Perm)."
        )

    return round(min(10.0, max(0.0, score)), 1), warnings, rationale


def evaluate_thermal(
    substrate: Dict[str, Any],
    intervention: Dict[str, Any]
) -> Tuple[float, List[str], str]:
    """Evaluate thermal dilation compatibility under diurnal temperature cycles."""
    warnings: List[str] = []
    sub_coeff = substrate.get("known_properties", {}).get("thermal_expansion_coeff_1e6_k")
    int_coeff = intervention.get("known_properties", {}).get("thermal_expansion_coeff_1e6_k")

    if sub_coeff is None:
        warnings.append("MISSING DATA: Substrate thermal expansion coefficient unknown; assumed 8.0 x 10^-6/K baseline.")
        sub_coeff = 8.0
    else:
        try:
            sub_coeff = float(sub_coeff)
        except (ValueError, TypeError):
            sub_coeff = 8.0

    if int_coeff is None:
        warnings.append("MISSING DATA: Intervention thermal expansion coefficient unknown; assumed 8.0 x 10^-6/K baseline.")
        int_coeff = 8.0
    else:
        try:
            int_coeff = float(int_coeff)
        except (ValueError, TypeError):
            int_coeff = 8.0

    delta = abs(sub_coeff - int_coeff)

    if delta > 20.0:
        score = 1.5
        rationale = (
            f"Severe thermal mismatch: Differential expansion delta ({delta:.1f} x 10^-6/K) between intervention "
            f"({int_coeff:.1f}) and host stone ({sub_coeff:.1f}) will induce interfacial shear delamination."
        )
        warnings.append(
            f"THERMAL EXPANSION MISMATCH: Intervention expansion ({int_coeff:.1f} x 10^-6/K) is drastically different "
            f"from host stone ({sub_coeff:.1f} x 10^-6/K). Rapid diurnal desert temperature swings will cause interfacial shear "
            f"delamination or tearing of the historic stone arrises."
        )
    elif delta > 8.0:
        score = 4.5
        rationale = (
            f"Moderate thermal strain: Thermal coefficient difference ({delta:.1f} x 10^-6/K) may induce micro-fissuring "
            f"along joint perimeters over repeated seasonal heating cycles."
        )
        warnings.append(
            f"ELEVATED THERMAL STRAIN: Significant expansion differential (delta: {delta:.1f} x 10^-6/K). "
            f"May cause micro-fissuring at the joint contact interface over multi-year cycles."
        )
    elif delta <= 3.0:
        score = 9.5
        rationale = (
            f"Thermal harmony: Coefficients are closely matched (delta: {delta:.1f} x 10^-6/K), preventing differential "
            f"thermal shearing across interfaces."
        )
    else:
        score = 7.5
        rationale = (
            f"Acceptable thermal dilation matching (delta: {delta:.1f} x 10^-6/K) for regional diurnal range."
        )

    return round(min(10.0, max(0.0, score)), 1), warnings, rationale


def evaluate_chemical(
    substrate: Dict[str, Any],
    intervention: Dict[str, Any]
) -> Tuple[float, List[str], str]:
    """Evaluate chemical inertness, autogenous healing, and absence of destructive salts."""
    warnings: List[str] = []
    int_fam = intervention.get("material_family", "").lower()
    int_id = intervention.get("material_id", "").lower()

    if "cement" in int_fam or "cement" in int_id or "opc" in int_id:
        score = 2.0
        rationale = (
            "Severe chemical incompatibility: Modern Portland cement hydration releases free sodium/potassium alkalis "
            "and sulfates that react with calcium carbonates to form expansive ettringite and thaumasite."
        )
        warnings.append(
            "CHEMICAL INCOMPATIBILITY: Cement hydration releases soluble sodium/potassium hydroxides and sulfates. "
            "These react with calcium carbonates in historic lime and sandstone to form expansive ettringite and "
            "thaumasite mineral phases, inducing destructive internal crystallization pressure."
        )
    elif "filler" in int_fam or "acrylic" in int_id or "epoxy" in int_id:
        score = 2.5
        rationale = (
            "Synthetic chemical degradation: Acrylic and epoxy polymers undergo embrittlement and photo-oxidation "
            "under solar UV and continuous subterranean dampness, releasing harmful degradation products."
        )
        warnings.append(
            "SYNTHETIC RESIN DEGRADATION: Organic polymers degrade under solar ultraviolet radiation and subterranean dampness, "
            "releasing organic degradation by-products and forming yellow, embrittled cross-linked crusts."
        )
    elif "lime" in int_fam:
        score = 9.5
        rationale = (
            "Chemical compatibility confirmed: Pure calcium-hydroxide binder provides high alkaline passivation, "
            "zero deleterious soluble sulfates, and autogenous self-healing of microcracks via carbonation."
        )
    else:
        score = 7.0
        rationale = "General chemical inertness observed; laboratory testing required to verify absence of soluble salts."

    return round(min(10.0, max(0.0, score)), 1), warnings, rationale


def evaluate_reversibility(
    intervention: Dict[str, Any]
) -> Tuple[float, List[str], str]:
    """Evaluate retreatability and reversibility without loss of historic substrate."""
    warnings: List[str] = []
    rev_data = intervention.get("reversibility", {})
    if not isinstance(rev_data, dict) or "reversibility_score" not in rev_data:
        warnings.append("MISSING DATA: Intervention reversibility data not specified; assuming moderate baseline score 5.0.")
        score = 5.0
    else:
        try:
            score = float(rev_data.get("reversibility_score", 5.0))
        except (ValueError, TypeError):
            score = 5.0

    if score < 4.0:
        rationale = (
            f"Critically non-reversible ({score}/10): Future extraction requires destructive mechanical percussion "
            f"that permanently fractures the adjoining historic stone units."
        )
        warnings.append(
            f"NON-REVERSIBLE INTERVENTION: Reversibility score ({score}/10) is critically low. Future removal requires "
            f"destructive mechanical cutting that inevitably damages original historic fabric, violating international conservation ethics."
        )
    elif score >= 8.0:
        rationale = (
            f"Fully retreatable ({score}/10): Traditional joint can be raked out with manual hand tools without "
            f"damaging original stone arrises, fully conforming to Venice and INTACH Charters."
        )
    else:
        rationale = f"Moderately retreatable ({score}/10); requires careful manual workmanship during future conservation cycles."

    return round(min(10.0, max(0.0, score)), 1), warnings, rationale


def evaluate_heritage(
    substrate: Dict[str, Any],
    intervention: Dict[str, Any]
) -> Tuple[float, List[str], str]:
    """Evaluate alignment with traditional IKS construction methods and ASI/INTACH ethics."""
    warnings: List[str] = []
    int_fam = intervention.get("material_family", "").lower()
    int_id = intervention.get("material_id", "").lower()

    if "surkhi" in int_id:
        score = 9.8
        rationale = (
            "Exemplary IKS authenticity: Authentic lime-surkhi hydraulic pozzolana matches ancient Indian water-harvesting "
            "construction traditions documented across Gujarat, Rajasthan, and Delhi (IS 3115 / CPWD Heritage Handbook)."
        )
    elif "lime" in int_fam:
        score = 9.0
        rationale = "High heritage alignment: Conforms to traditional slaked lime masonry practices recognized by ASI and INTACH."
    elif "cement" in int_fam or "opc" in int_id:
        score = 1.0
        rationale = "Policy & ethical violation: Portland cement on historic monuments is prohibited by ASI and INTACH Charters."
        warnings.append(
            "ETHICAL & POLICY VIOLATION: Portland cement rendering on historic monuments is explicitly prohibited by the "
            "ASI Conservation Manual (2020) and INTACH Charter (2004)."
        )
    elif "filler" in int_fam or "acrylic" in int_id or "epoxy" in int_id:
        score = 1.5
        rationale = "Alien synthetic material: Non-traditional industrial polymer lacking historical or craftsmanship authenticity."
        warnings.append("ALIEN MATERIAL: Synthetic fillers lack historical authenticity and indigenous craftsmanship alignment.")
    else:
        score = 6.0
        rationale = "Neutral heritage alignment; material requires site-specific architectural conservation review."

    return round(min(10.0, max(0.0, score)), 1), warnings, rationale


def evaluate_visual(
    substrate: Dict[str, Any],
    intervention: Dict[str, Any]
) -> Tuple[float, List[str], str]:
    """Evaluate visual texture, color, and aging compatibility."""
    warnings: List[str] = []
    int_fam = intervention.get("material_family", "").lower()
    int_id = intervention.get("material_id", "").lower()

    if "surkhi" in int_id:
        score = 9.2
        rationale = "Visual harmony: Warm terracotta surkhi blends seamlessly with historic sandstone and weathered patinas."
    elif "lime" in int_fam:
        score = 8.5
        rationale = "Visual compatibility: Natural off-white and buff lime tones age gracefully alongside historic masonry."
    elif "cement" in int_fam or "opc" in int_id:
        score = 2.0
        rationale = "Severe visual clash: Dull grey industrial cement creates stark, unsightly scars across warm historic stone."
        warnings.append("VISUAL DISHARMONY: Cold grey cement matrix contrasts harshly with warm, patinated historic stone.")
    elif "filler" in int_fam or "acrylic" in int_id or "epoxy" in int_id:
        score = 2.5
        rationale = "Artificial visual appearance: Synthetic polymer yields unnatural plastic sheen and darkens with age."
        warnings.append("ARTIFICIAL GLOSS: Synthetic polymer creates an unnatural plastic sheen incompatible with historic stone texture.")
    else:
        score = 7.0
        rationale = "Acceptable visual integration; on-site aggregate color-matching test panels recommended."

    return round(min(10.0, max(0.0, score)), 1), warnings, rationale


def compute_composite_compatibility(
    dimensions: Dict[str, float],
    original_material_confidence: Optional[float] = None,
) -> Tuple[float, str, List[str]]:
    """Calculate weighted composite compatibility score and map to conservation recommendation.

    Notes on limitations:
    - This score is a risk-ranked screening metric, NOT a laboratory certification.
    - If substrate identification confidence is low (<0.60), the recommendation is capped
      at 'acceptable_conditional' to prevent automated prescription of definitive repair mixes.
    """
    score_out_of_100 = 0.0
    for dim_name, weight in COMPATIBILITY_WEIGHTS.items():
        dim_score = dimensions.get(dim_name, 5.0)
        # Each dimension is 0-10, so dim_score * 10 gives a 0-100 scale component
        score_out_of_100 += (dim_score * 10.0) * weight

    score_out_of_100 = round(min(100.0, max(0.0, score_out_of_100)), 1)
    advisories: List[str] = []

    if score_out_of_100 >= 80.0:
        recommendation = "strongly_recommended"
    elif score_out_of_100 >= 65.0:
        recommendation = "recommended"
    elif score_out_of_100 >= 45.0:
        recommendation = "acceptable_conditional"
    else:
        recommendation = "prohibited_incompatible"

    # Enforce conservation safety guard: never strongly recommend a definitive mixture
    # when substrate identity has low confidence (< 0.60) or is unverified photographic guesswork.
    if original_material_confidence is not None and original_material_confidence < 0.60:
        if recommendation in ["strongly_recommended", "recommended"]:
            recommendation = "acceptable_conditional"
            advisories.append(
                f"SAFETY CAP APPLIED: Recommendation capped at 'acceptable_conditional' due to low substrate identification "
                f"confidence ({original_material_confidence:.2f}). Photographic evidence is insufficient for definitive mortar formulation; "
                f"on-site laboratory petrography is mandatory before specifying final mix proportions."
            )

    return score_out_of_100, recommendation, advisories
