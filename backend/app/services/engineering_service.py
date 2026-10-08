"""Engineering Assessment Service implementing deterministic conservation rules.

Maintained by Swastik Parmar (Backend / Integration Engineer).
Integrates Kirti Antil's IKS conservation engineering engine.
Adheres strictly to contracts/engineering_result.schema.json.

IMPORTANT CONSERVATION PRINCIPLE:
Outputs are decision-support triage scores for heritage conservation planning.
They are NOT certified structural safety assessments.
"""

from typing import Any, Dict, List, Optional

from backend.app.schemas.engineering import (
    EngineeringResult,
)
from backend.app.schemas.vision import VisionResult
from engineering import (
    DEFAULT_ENGINEERING_DISCLAIMER,
    ConservationEngineeringService,
    analyze_heritage_structure,
)


def _normalize_vision_dict(vision_dict: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Sanitize vision dictionary ensuring non-null relative_severity for scoring."""
    if not vision_dict or not isinstance(vision_dict, dict):
        return vision_dict
    normalized = dict(vision_dict)
    detections = normalized.get("detections")
    if isinstance(detections, list):
        cleaned_detections = []
        for d in detections:
            if isinstance(d, dict):
                d_copy = dict(d)
                if not d_copy.get("relative_severity"):
                    d_copy["relative_severity"] = "moderate"
                cleaned_detections.append(d_copy)
            else:
                cleaned_detections.append(d)
        normalized["detections"] = cleaned_detections
    return normalized


class EngineeringService:
    """Service executing deterministic rules on visual defect measurements and inspection data."""

    MANDATORY_DISCLAIMER: str = DEFAULT_ENGINEERING_DISCLAIMER

    def __init__(self) -> None:
        self._engineering_facade = ConservationEngineeringService()

    def assess_vision_result(
        self,
        vision_result: VisionResult,
        structure_name: Optional[str] = None,
        region: Optional[str] = None,
        inspection_data: Optional[Dict[str, Any]] = None,
        inferred_material: Optional[str] = None,
        material_confidence: Optional[float] = None,
        candidate_materials: Optional[List[str]] = None,
        recent_repair_type: Optional[str] = None,
    ) -> EngineeringResult:
        """Calculate deterministic condition, functionality, and restoration priority scores."""
        struct_type = (
            vision_result.structure_type.value
            if hasattr(vision_result.structure_type, "value")
            else str(vision_result.structure_type)
        )
        vision_dict = _normalize_vision_dict(vision_result.model_dump())

        analysis_dict = analyze_heritage_structure(
            structure_type=struct_type,
            vision_data=vision_dict,
            inspection_data=inspection_data,
            inferred_material=inferred_material,
            material_confidence=material_confidence,
            candidate_materials=candidate_materials,
            recent_repair_type=recent_repair_type,
        )

        eng_payload = analysis_dict["engineering_result"]
        return EngineeringResult.model_validate(eng_payload)

    def assess_full_structure(
        self,
        structure_type: Optional[str] = None,
        vision_data: Optional[Dict[str, Any]] = None,
        inspection_data: Optional[Dict[str, Any]] = None,
        inferred_material: Optional[str] = None,
        material_confidence: Optional[float] = None,
        candidate_materials: Optional[List[str]] = None,
        recent_repair_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Perform end-to-end engineering, material compatibility, and restoration planning."""
        normalized_vision = _normalize_vision_dict(vision_data)
        return self._engineering_facade.analyze_structure(
            structure_type=structure_type,
            vision_data=normalized_vision,
            inspection_data=inspection_data,
            inferred_material=inferred_material,
            material_confidence=material_confidence,
            candidate_materials=candidate_materials,
            recent_repair_type=recent_repair_type,
        )


engineering_service = EngineeringService()
