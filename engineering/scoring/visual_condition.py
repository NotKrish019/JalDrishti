"""Deterministic Visual Condition Scoring for Jaldrishti heritage conservation.

Consumes visual defect observations from the vision subsystem (cracks, vegetation,
spalling, stone dislodgement) and calculates transparent condition indices conforming to
/contracts/engineering_result.schema.json.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union


DEFAULT_LIMITATIONS = [
    "Score is derived strictly from 2D surface photographic defect coverage.",
    "Internal masonry voids, foundation settlement, and subterranean structural stability cannot be verified from surface imagery.",
    "Field calibration with ultrasonic pulse velocity (UPV) and endoscopy is recommended for critical structural elements.",
]


class VisualConditionScorer:
    """Calculates deterministic condition scores from defect burdens and vision detections."""

    SEVERITY_FACTORS: Dict[str, float] = {
        "low": 0.8,
        "moderate": 1.2,
        "severe": 1.8,
    }

    DEFECT_WEIGHTS: Dict[str, float] = {
        "crack": 1.5,
        "vegetation_root_intrusion": 1.6,
        "vegetation": 1.4,
        "spalling": 1.2,
        "stone_dislodgement": 2.0,
        "biological_growth": 0.6,
        "efflorescence": 0.8,
    }

    def __init__(self) -> None:
        pass

    def extract_defect_metrics(
        self,
        detections: Optional[List[Dict[str, Any]]] = None,
        crack_burden: Optional[float] = None,
        vegetation_burden: Optional[float] = None,
        spalling_burden: Optional[float] = None,
        dislodgement_burden: Optional[float] = None,
    ) -> Dict[str, Dict[str, float]]:
        """Normalize visual detections or direct defect parameters into a uniform defect map."""
        defect_map: Dict[str, Dict[str, float]] = {
            "crack": {"coverage": 0.0, "severity_factor": 1.0, "confidence": 0.8},
            "vegetation": {"coverage": 0.0, "severity_factor": 1.0, "confidence": 0.8},
            "spalling": {"coverage": 0.0, "severity_factor": 1.0, "confidence": 0.8},
            "dislodgement": {"coverage": 0.0, "severity_factor": 1.0, "confidence": 0.8},
        }

        # Override with direct scalar inputs if provided
        if crack_burden is not None:
            defect_map["crack"]["coverage"] = min(1.0, max(0.0, float(crack_burden)))
        if vegetation_burden is not None:
            defect_map["vegetation"]["coverage"] = min(1.0, max(0.0, float(vegetation_burden)))
        if spalling_burden is not None:
            defect_map["spalling"]["coverage"] = min(1.0, max(0.0, float(spalling_burden)))
        if dislodgement_burden is not None:
            defect_map["dislodgement"]["coverage"] = min(1.0, max(0.0, float(dislodgement_burden)))

        # Process structured detections from vision payload
        if detections:
            for det in detections:
                c_name = det.get("class_name", "").lower()
                cov = float(det.get("coverage_ratio", 0.0))
                sev = det.get("relative_severity", "moderate").lower()
                sev_factor = self.SEVERITY_FACTORS.get(sev, 1.0)
                conf = float(det.get("confidence", 0.75))

                if "crack" in c_name:
                    defect_map["crack"]["coverage"] += cov
                    defect_map["crack"]["severity_factor"] = max(defect_map["crack"]["severity_factor"], sev_factor)
                    defect_map["crack"]["confidence"] = min(defect_map["crack"]["confidence"], conf)
                elif "vegetation" in c_name or "root" in c_name:
                    defect_map["vegetation"]["coverage"] += cov
                    defect_map["vegetation"]["severity_factor"] = max(defect_map["vegetation"]["severity_factor"], sev_factor)
                    defect_map["vegetation"]["confidence"] = min(defect_map["vegetation"]["confidence"], conf)
                elif "spall" in c_name:
                    defect_map["spalling"]["coverage"] += cov
                    defect_map["spalling"]["severity_factor"] = max(defect_map["spalling"]["severity_factor"], sev_factor)
                    defect_map["spalling"]["confidence"] = min(defect_map["spalling"]["confidence"], conf)
                elif "dislodg" in c_name:
                    defect_map["dislodgement"]["coverage"] += cov
                    defect_map["dislodgement"]["severity_factor"] = max(defect_map["dislodgement"]["severity_factor"], sev_factor)
                    defect_map["dislodgement"]["confidence"] = min(defect_map["dislodgement"]["confidence"], conf)

        # Cap coverage at 1.0
        for k in defect_map:
            defect_map[k]["coverage"] = min(1.0, defect_map[k]["coverage"])

        return defect_map

    def calculate_score(
        self,
        detections: Optional[List[Dict[str, Any]]] = None,
        crack_burden: Optional[float] = None,
        vegetation_burden: Optional[float] = None,
        spalling_burden: Optional[float] = None,
        dislodgement_burden: Optional[float] = None,
        confidence_override: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Calculate primary visual condition score and sub-scores.

        Scale: 0.0 (catastrophically degraded) to 100.0 (pristine sound condition).
        """
        defect_map = self.extract_defect_metrics(
            detections=detections,
            crack_burden=crack_burden,
            vegetation_burden=vegetation_burden,
            spalling_burden=spalling_burden,
            dislodgement_burden=dislodgement_burden,
        )

        # Calculate deduct points per defect category
        crack_deduct = min(35.0, defect_map["crack"]["coverage"] * 100.0 * 1.5 * defect_map["crack"]["severity_factor"])
        veg_deduct = min(35.0, defect_map["vegetation"]["coverage"] * 100.0 * 1.6 * defect_map["vegetation"]["severity_factor"])
        spall_deduct = min(25.0, defect_map["spalling"]["coverage"] * 100.0 * 1.2 * defect_map["spalling"]["severity_factor"])
        dislodge_deduct = min(40.0, defect_map["dislodgement"]["coverage"] * 100.0 * 2.0 * defect_map["dislodgement"]["severity_factor"])

        total_deduct = min(95.0, crack_deduct + veg_deduct + spall_deduct + dislodge_deduct)
        condition_value = round(max(5.0, 100.0 - total_deduct), 1)

        # Calculate sub-indices (higher = better condition)
        veg_integrity = round(max(5.0, 100.0 - (veg_deduct * 2.8)), 1)
        masonry_integrity = round(max(5.0, 100.0 - ((crack_deduct + spall_deduct + dislodge_deduct) * 1.4)), 1)

        # Average confidence across observed defects
        if confidence_override is not None:
            confidence = min(0.95, max(0.2, float(confidence_override)))
        else:
            conf_list = [d["confidence"] for d in defect_map.values() if d["coverage"] > 0]
            confidence = round(sum(conf_list) / len(conf_list), 2) if conf_list else 0.85

        return {
            "visual_condition_score": {
                "value": condition_value,
                "scale_min": 0.0,
                "scale_max": 100.0,
                "method": "deterministic_visual_deduct_model_v1",
                "confidence": confidence,
                "limitations": list(DEFAULT_LIMITATIONS),
            },
            "sub_scores": {
                "vegetation_intrusion_index": {
                    "value": veg_integrity,
                    "scale_min": 0.0,
                    "scale_max": 100.0,
                    "method": "vegetation_coverage_severity_deduct_v1",
                    "confidence": confidence,
                    "limitations": [
                        "Measures visible external root and vegetation foliage coverage; deep root penetration depth requires endoscopic probing."
                    ],
                },
                "masonry_integrity_index": {
                    "value": masonry_integrity,
                    "scale_min": 0.0,
                    "scale_max": 100.0,
                    "method": "masonry_fracture_spall_dislodgement_deduct_v1",
                    "confidence": confidence,
                    "limitations": [
                        "Evaluates visible surface crack apertures and stone spalls; subsurface stress distribution requires non-destructive testing."
                    ],
                },
            },
            "deduct_breakdown": {
                "crack_deduct": round(crack_deduct, 1),
                "vegetation_deduct": round(veg_deduct, 1),
                "spalling_deduct": round(spall_deduct, 1),
                "dislodgement_deduct": round(dislodge_deduct, 1),
                "total_deduct": round(total_deduct, 1),
            },
        }


default_visual_scorer = VisualConditionScorer()


def calculate_visual_condition(
    detections: Optional[List[Dict[str, Any]]] = None,
    crack_burden: Optional[float] = None,
    vegetation_burden: Optional[float] = None,
    spalling_burden: Optional[float] = None,
    dislodgement_burden: Optional[float] = None,
    confidence: Optional[float] = None,
) -> Dict[str, Any]:
    """Convenience functional interface for visual condition scoring."""
    return default_visual_scorer.calculate_score(
        detections=detections,
        crack_burden=crack_burden,
        vegetation_burden=vegetation_burden,
        spalling_burden=spalling_burden,
        dislodgement_burden=dislodgement_burden,
        confidence_override=confidence,
    )
