"""Unified Analysis Orchestration Service.

Maintained by Swastik Parmar (Backend / Integration Engineer).
Adheres strictly to contracts/analysis.schema.json.

Orchestration flow:
Frontend Request -> Vision Service -> Engineering Service -> IKS / Material Context -> AnalysisResult
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.schemas.analysis import (
    AnalysisMetadata,
    AnalysisResult,
    PipelineStatus,
    StructureInfo,
    StructureTypeEnum,
)
from backend.app.schemas.engineering import ScoreMetric
from backend.app.schemas.material import MaterialCompatibilityResult
from backend.app.schemas.restoration import RestorationResult
from backend.app.schemas.vision import (
    DetectionItem,
    ImageDimensions,
    ScaleReference,
    StructureType,
    VisionResult,
)
from backend.app.services.engineering_service import engineering_service
from backend.app.services.vision_service import vision_service


class AnalysisService:
    """Orchestrates end-to-end multi-disciplinary conservation pipeline."""

    def orchestrate_analysis(
        self,
        structure_type: StructureType = StructureType.BAOLI,
        name: Optional[str] = "Heritage Stepwell",
        region: Optional[str] = "Rajasthan, India",
        source_images: Optional[List[str]] = None,
        image_bytes: Optional[bytes] = None,
        image_dimensions: Optional[ImageDimensions] = None,
        scale_reference: Optional[ScaleReference] = None,
        detections: Optional[List[DetectionItem]] = None,
        inspection_data: Optional[Dict[str, Any]] = None,
        inferred_material: Optional[str] = None,
        material_confidence: Optional[float] = None,
        candidate_materials: Optional[List[str]] = None,
        recent_repair_type: Optional[str] = None,
        roi_box: Optional[List[float]] = None,
    ) -> AnalysisResult:
        """Run full vision and engineering pipeline and synthesize unified AnalysisResult.

        Args:
            structure_type: Structural typology.
            name: Monument designation.
            region: Geographical location.
            source_images: List of source asset URIs.
            image_bytes: Optional raw image byte payload.
            image_dimensions: Optional image resolution.
            scale_reference: Optional metric calibration scale.
            detections: Pre-detected or manually noted defects.
            inspection_data: Hydrological indicators (inlet, outlet, siltation, etc.).
            inferred_material: Optional substrate identification.
            material_confidence: Confidence of substrate identification.
            candidate_materials: Candidate intervention materials to evaluate.
            recent_repair_type: Modern repair observed on site.
            roi_box: Optional user-selected bounding region [x, y, w, h].

        Returns:
            AnalysisResult: Full validated contract instance.
        """
        resolved_images = source_images if source_images else ["survey_image_01.jpg"]

        # Step 1: Vision Inference / Defect Extraction
        vision_result: VisionResult = vision_service.analyze_image(
            image_bytes=image_bytes,
            image_name=resolved_images[0] if resolved_images else None,
            source_images=resolved_images,
            structure_type=structure_type,
            image_dimensions=image_dimensions,
            scale_reference=scale_reference,
            detections=detections,
            roi_box=roi_box,
        )

        # Step 2: Engineering Assessment & IKS Material/Restoration Analysis
        struct_res = engineering_service.assess_full_structure(
            structure_type=structure_type.value,
            vision_data=vision_result.model_dump(),
            inspection_data=inspection_data,
            inferred_material=inferred_material,
            material_confidence=material_confidence,
            candidate_materials=candidate_materials,
            recent_repair_type=recent_repair_type,
        )

        # Step 3: Material Compatibility from Engineering Module
        material_result = MaterialCompatibilityResult.model_validate(
            struct_res["material"]
        )

        # Step 4: Phased Restoration Roadmap from Engineering Module
        restoration_result = RestorationResult.model_validate(
            struct_res["restoration"]
        )

        # Step 5: Root Cause Analysis Object
        root_causes_list = struct_res.get("root_cause", [])
        primary_finding = (
            root_causes_list[0]["probable_cause"] if root_causes_list else "None detected"
        )
        root_cause_obj = {
            "findings": root_causes_list,
            "primary_cause": primary_finding,
            "count": len(root_causes_list),
        }

        # Step 6: Assemble Unified Analysis Result
        return AnalysisResult(
            project_version="0.1.0",
            structure=StructureInfo(
                type=StructureTypeEnum(structure_type.value),
                name=name,
                region=region,
                source_images=resolved_images,
            ),
            vision=vision_result,
            visual_condition=ScoreMetric.model_validate(
                struct_res["visual_condition"]
            ),
            water_functionality=ScoreMetric.model_validate(
                struct_res["water_functionality"]
            ),
            material=material_result,
            root_cause=root_cause_obj,
            restoration=restoration_result,
            metadata=AnalysisMetadata(
                created_at=datetime.now(timezone.utc).isoformat(),
                pipeline_status=PipelineStatus.COMPLETED,
                orchestrated_by="JalDrishti Multi-Disciplinary Orchestrator",
            ),
        )


analysis_service = AnalysisService()
