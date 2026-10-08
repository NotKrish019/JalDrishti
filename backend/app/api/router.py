"""API router definition for JalDrishti backend.

Maintained by Swastik Parmar (Backend / Integration Engineer).
Integrates live Vision, Engineering, Material Compatibility, Restoration Planning,
and Knowledge subsystems.
"""

import json
from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, Body, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from backend.app.schemas.analysis import AnalysisResult
from backend.app.schemas.engineering import EngineeringResult
from backend.app.schemas.health import HealthResponse
from backend.app.schemas.material import MaterialCompatibilityResult
from backend.app.schemas.requests import (
    AnalysisPipelineRequest,
    EngineeringAssessmentRequest,
    MaterialCompatibilityRequest,
    RestorationPlanRequest,
)
from backend.app.schemas.restoration import RestorationResult
from backend.app.schemas.vision import StructureType, VisionResult
from backend.app.services.analysis_service import analysis_service
from backend.app.services.engineering_service import engineering_service
from backend.app.services.vision_service import vision_service
from engineering import (
    default_repository,
    evaluate_compatibility,
    get_source,
    get_structure,
    list_structures,
    plan_restoration,
)

api_router = APIRouter()


@api_router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Verify backend service readiness and runtime configuration.",
    tags=["System"],
)
def get_health() -> HealthResponse:
    """Return service health and version metadata."""
    return HealthResponse(
        status="ok",
        project="jaldrishti",
        version="0.1.0",
    )


# -----------------------------------------------------------------------------
# Vision & Engineering Pipeline Endpoints
# -----------------------------------------------------------------------------


async def _extract_pipeline_request(
    request: Request,
) -> tuple[AnalysisPipelineRequest, Optional[bytes], Optional[List[float]]]:
    """Parse incoming pipeline request supporting both JSON payloads and multipart/form-data."""
    content_type = request.headers.get("content-type", "")
    image_bytes: Optional[bytes] = None
    roi_box: Optional[List[float]] = None

    if "application/json" in content_type:
        try:
            body_json = await request.json()
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid JSON body") from exc
        try:
            req_model = AnalysisPipelineRequest.model_validate(body_json)
        except ValidationError as e:
            raise RequestValidationError(e.errors()) from e
        return req_model, None, None

    # Handle multipart/form-data or application/x-www-form-urlencoded
    form = await request.form()
    uploaded_file = form.get("images")
    source_images: List[str] = ["survey_image_01.jpg"]

    if uploaded_file is not None and hasattr(uploaded_file, "read"):
        image_bytes = await uploaded_file.read()
        fname = getattr(uploaded_file, "filename", None)
        if fname:
            source_images = [fname]
    elif isinstance(uploaded_file, str) and uploaded_file:
        source_images = [uploaded_file]

    roi_str = form.get("roi_box")
    if roi_str:
        try:
            roi_box = json.loads(str(roi_str))
        except Exception:
            roi_box = None

    st_raw = form.get("structure_type", "baoli")
    try:
        st_enum = StructureType(st_raw)
    except ValueError:
        st_enum = StructureType.BAOLI

    req_dict: Dict[str, Any] = {
        "structure_type": st_enum,
        "name": form.get("name") or "Heritage Water Structure",
        "region": form.get("region") or "Northern India",
        "source_images": source_images,
    }

    notes = form.get("notes")
    if notes:
        req_dict["inspection_data"] = {"notes": notes}

    try:
        req_model = AnalysisPipelineRequest.model_validate(req_dict)
    except ValidationError as e:
        raise RequestValidationError(e.errors()) from e

    return req_model, image_bytes, roi_box


@api_router.post(
    "/vision/analyze",
    response_model=VisionResult,
    status_code=status.HTTP_200_OK,
    summary="Vision Defect Analysis",
    description="Extract and normalize image-space defect segments from JSON or multipart image uploads.",
    tags=["Vision"],
)
async def analyze_vision(
    request: Request,
) -> VisionResult:
    """Run computer vision defect extraction and spatial analysis."""
    req_model, image_bytes, roi_box = await _extract_pipeline_request(request)
    return vision_service.analyze_image(
        image_bytes=image_bytes,
        image_name=req_model.source_images[0] if req_model.source_images else None,
        source_images=req_model.source_images,
        structure_type=req_model.structure_type,
        image_dimensions=req_model.image_dimensions,
        scale_reference=req_model.scale_reference,
        detections=req_model.detections,
        roi_box=roi_box,
    )


@api_router.post(
    "/engineering",
    response_model=EngineeringResult,
    status_code=status.HTTP_200_OK,
    summary="Engineering Assessment",
    description="Calculate deterministic condition, functionality, and restoration priority scores.",
    tags=["Engineering"],
)
def assess_engineering(
    payload: Union[EngineeringAssessmentRequest, VisionResult] = Body(...),
) -> EngineeringResult:
    """Run deterministic engineering calculations on vision inspection outputs."""
    if isinstance(payload, EngineeringAssessmentRequest):
        if payload.vision is not None:
            vision_input = payload.vision
        else:
            st_type = payload.structure_type or StructureType.BAOLI
            vision_input = vision_service.analyze_image(
                structure_type=st_type,
                image_dimensions=payload.image_dimensions,
                detections=payload.detections,
            )
        return engineering_service.assess_vision_result(
            vision_result=vision_input,
            structure_name=payload.structure_name,
            region=payload.region,
            inspection_data=payload.inspection_data,
            inferred_material=payload.inferred_material,
            material_confidence=payload.material_confidence,
            candidate_materials=payload.candidate_materials,
            recent_repair_type=payload.recent_repair_type,
        )
    return engineering_service.assess_vision_result(vision_result=payload)


@api_router.post(
    "/material-compatibility",
    response_model=MaterialCompatibilityResult,
    status_code=status.HTTP_200_OK,
    summary="Material Compatibility Evaluation",
    description="Evaluate candidate intervention materials against historic substrates using deterministic rules.",
    tags=["Materials"],
)
def evaluate_material_compatibility(
    request: Optional[MaterialCompatibilityRequest] = Body(default=None),
) -> MaterialCompatibilityResult:
    """Evaluate candidate mortars and consolidants against historical substrates."""
    req = request or MaterialCompatibilityRequest()
    orig_mat = req.original_material
    if not orig_mat and req.structure_type:
        from engineering.service import TYPOLOGY_MATERIAL_DEFAULTS
        orig_mat = TYPOLOGY_MATERIAL_DEFAULTS.get(
            req.structure_type.value, "hydraulic_lime_mortar"
        )
    orig_mat = orig_mat or "hydraulic_lime_mortar"

    res_dict = evaluate_compatibility(
        original_material=orig_mat,
        candidate_materials=req.candidate_materials,
        original_material_confidence=req.original_material_confidence,
    )
    return MaterialCompatibilityResult.model_validate(res_dict)


@api_router.post(
    "/restore",
    response_model=RestorationResult,
    status_code=status.HTTP_200_OK,
    summary="Conservation Restoration Roadmap",
    description="Generate phased conservation interventions and traditional IKS restoration guidance.",
    tags=["Restoration"],
)
def generate_restoration_roadmap(
    request: Optional[RestorationPlanRequest] = Body(default=None),
) -> RestorationResult:
    """Plan phased conservation roadmap and apply IKS principles."""
    req = request or RestorationPlanRequest()
    st_val = req.structure_type.value if req.structure_type else "baoli"

    res_dict = plan_restoration(
        structure_type=st_val,
        visual_condition_score=req.visual_condition_score or 75.0,
        water_functionality_score=req.water_functionality_score or 60.0,
        crack_burden=req.crack_burden or 0.0,
        vegetation_burden=req.vegetation_burden or 0.0,
        spalling_burden=req.spalling_burden or 0.0,
        dislodgement_burden=req.dislodgement_burden or 0.0,
        siltation_level=req.siltation_level or "unknown",
        inlet_condition=req.inlet_condition or "unknown",
        inferred_material=req.inferred_material or "hydraulic_lime_mortar",
        root_causes=req.root_causes,
    )
    return RestorationResult.model_validate(res_dict)


@api_router.post(
    "/analyze",
    response_model=AnalysisResult,
    status_code=status.HTTP_200_OK,
    summary="Unified Analysis Pipeline",
    description="Orchestrates full end-to-end multi-disciplinary conservation pipeline from JSON or multipart form.",
    tags=["Pipeline"],
)
async def analyze_structure(
    request: Request,
) -> AnalysisResult:
    """Execute end-to-end inspection pipeline (Vision -> Engineering -> Unified Contract)."""
    req_model, image_bytes, roi_box = await _extract_pipeline_request(request)
    return analysis_service.orchestrate_analysis(
        structure_type=req_model.structure_type,
        name=req_model.name,
        region=req_model.region,
        source_images=req_model.source_images,
        image_bytes=image_bytes,
        image_dimensions=req_model.image_dimensions,
        scale_reference=req_model.scale_reference,
        detections=req_model.detections,
        inspection_data=req_model.inspection_data,
        inferred_material=req_model.inferred_material,
        material_confidence=req_model.material_confidence,
        candidate_materials=req_model.candidate_materials,
        recent_repair_type=req_model.recent_repair_type,
        roi_box=roi_box,
    )


# -----------------------------------------------------------------------------
# Knowledge Base Lookup Endpoints
# -----------------------------------------------------------------------------


@api_router.get(
    "/knowledge/structures",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="List Known Water Structures",
    description="Retrieve all traditional water structure typology definitions and architectural profiles.",
    tags=["Knowledge"],
)
def get_known_structures() -> List[Dict[str, Any]]:
    """Return all catalogued water structure typologies."""
    return list_structures()


@api_router.get(
    "/knowledge/structures/{structure_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get Structure Knowledge Details",
    description="Retrieve deep architectural, hydrological, and conservation metadata for a specific typology.",
    tags=["Knowledge"],
)
def get_structure_details(structure_id: str) -> Dict[str, Any]:
    """Return specific structure typology knowledge record."""
    try:
        return get_structure(structure_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Structure typology '{structure_id}' not found.",
        ) from exc


@api_router.get(
    "/knowledge/sources",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="List Literature and Research Sources",
    description="Retrieve references and academic sources underpinning conservation logic.",
    tags=["Knowledge"],
)
def get_literature_sources() -> List[Dict[str, Any]]:
    """Return bibliographic and heritage guidelines source catalog."""
    return default_repository.list_sources()
