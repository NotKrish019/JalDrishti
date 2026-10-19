"""API router definition for JalDrishti backend.

Maintained by Swastik Parmar (Backend / Integration Engineer).
Integrates live Vision, Engineering, Material Compatibility, Restoration Planning,
and Knowledge subsystems.
"""

from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional, Union
import uuid

from fastapi import (
    APIRouter,
    Body,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from backend.app.core.config import settings
from backend.app.db.image_repository import (
    MetadataPersistenceError,
    image_repository,
)
from backend.app.schemas.analysis import AnalysisResult
from backend.app.schemas.engineering import EngineeringResult
from backend.app.schemas.health import HealthResponse
from backend.app.schemas.image import (
    ImageDeleteResponse,
    ImageMetadata,
    ImageUploadResponse,
    InspectionImagesListResponse,
)
from backend.app.schemas.material import MaterialCompatibilityResult
from backend.app.schemas.requests import (
    AnalysisPipelineRequest,
    EngineeringAssessmentRequest,
    MaterialCompatibilityRequest,
    RestorationPlanRequest,
)
from backend.app.schemas.restoration import RestorationResult
from backend.app.schemas.vision import ImageDimensions, StructureType, VisionResult
from backend.app.services.analysis_service import analysis_service
from backend.app.services.cloudinary_service import (
    CloudinaryConfigError,
    CloudinaryDeleteError,
    CloudinaryUploadError,
    cloudinary_service,
)
from backend.app.services.engineering_service import engineering_service
from backend.app.services.vision_service import vision_service
from backend.app.utils.image_validator import (
    ImageDecodeError,
    ImageEmptyError,
    ImageFormatError,
    ImageSizeLimitError,
    ImageValidationError,
    read_and_validate_image_upload,
)
from engineering import (
    default_repository,
    evaluate_compatibility,
    get_source,
    get_structure,
    list_structures,
    plan_restoration,
)

logger = logging.getLogger(__name__)

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

        # If registered image_id is referenced, resolve metadata from repository
        if req_model.image_id:
            record = image_repository.get_by_id(req_model.image_id)
            if record:
                if req_model.source_images == ["survey_image_01.jpg"]:
                    req_model.source_images = [record.preview_url]
                if req_model.image_dimensions is None:
                    req_model.image_dimensions = ImageDimensions(
                        width_pixels=record.width,
                        height_pixels=record.height,
                    )
        return req_model, None, None

    # Handle multipart/form-data or application/x-www-form-urlencoded
    form = await request.form()
    uploaded_file = form.get("images") or form.get("file") or form.get("image")
    source_images: List[str] = ["survey_image_01.jpg"]

    form_image_id = form.get("image_id")
    resolved_dims: Optional[ImageDimensions] = None
    if form_image_id and isinstance(form_image_id, str):
        record = image_repository.get_by_id(form_image_id)
        if record:
            source_images = [record.preview_url]
            resolved_dims = ImageDimensions(
                width_pixels=record.width,
                height_pixels=record.height,
            )

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

    if form_image_id and isinstance(form_image_id, str):
        req_dict["image_id"] = form_image_id
    if resolved_dims is not None:
        req_dict["image_dimensions"] = resolved_dims

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


# -----------------------------------------------------------------------------
# Image Ingestion & Storage Endpoints (Cloudinary & Local Durability)
# -----------------------------------------------------------------------------


@api_router.post(
    "/images/upload",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Inspection Image",
    description=(
        "Uploads an inspection photograph through a backend-controlled workflow. "
        "Enforces streaming bounded reads, validates format and content decodability via Pillow, "
        "uploads to Cloudinary without exposing credentials, and durably records metadata."
    ),
    tags=["Images"],
)
async def upload_inspection_image(
    request: Request,
    file: Optional[UploadFile] = File(default=None),
    images: Optional[UploadFile] = File(default=None),
    image: Optional[UploadFile] = File(default=None),
    inspection_id: Optional[str] = Form(default=None),
    structure_type: Optional[str] = Form(default=None),
    structure_name: Optional[str] = Form(default=None),
    notes: Optional[str] = Form(default=None),
) -> ImageUploadResponse:
    """Accept and validate image upload, store to Cloudinary, and persist metadata."""
    # Resolve uploaded file from available multipart fields
    target_file = file or images or image

    if target_file is None:
        # Check form dynamically in case of non-standard field naming
        try:
            form = await request.form()
            for key, val in form.items():
                if hasattr(val, "read") and hasattr(val, "filename"):
                    target_file = val
                    break
        except Exception:
            pass

    if target_file is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No image file provided in multipart request. Use 'file' or 'images' form field.",
        )

    # 1. Bounded streaming read and strict image validation
    try:
        image_bytes, format_str, width, height = await read_and_validate_image_upload(
            target_file,
            max_size_bytes=settings.max_upload_size_bytes,
            allowed_formats=settings.allowed_image_formats,
        )
    except ImageEmptyError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ImageSizeLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail=str(e)
        )
    except ImageFormatError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ImageDecodeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ImageValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # 2. Check Cloudinary configuration
    if not cloudinary_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Image storage service is not configured. "
                "Required backend environment variables: "
                "CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET."
            ),
        )

    # 3. Generate stable identifiers
    gen_image_id = f"img_{uuid.uuid4()}"
    assigned_inspection_id = inspection_id or f"insp_{uuid.uuid4()}"
    public_id = f"{settings.cloudinary_folder}/{gen_image_id}"

    # 4. Upload to Cloudinary
    tags = ["jaldrishti", "heritage_water_structure"]
    if structure_type:
        tags.append(structure_type.lower())

    context = {
        "image_id": gen_image_id,
        "inspection_id": assigned_inspection_id,
    }
    if structure_name:
        context["structure_name"] = structure_name

    try:
        upload_res = cloudinary_service.upload_image(
            image_bytes=image_bytes,
            public_id=public_id,
            folder=settings.cloudinary_folder,
            tags=tags,
            context=context,
        )
    except CloudinaryConfigError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
    except CloudinaryUploadError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cloudinary image upload failed. Please verify storage availability and try again.",
        )
    except Exception as e:
        logger.error("Unexpected upload failure: %s", type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error processing image upload.",
        )

    # 5. Assemble persistent metadata
    now_iso = datetime.now(timezone.utc).isoformat()
    metadata = ImageMetadata(
        image_id=gen_image_id,
        inspection_id=assigned_inspection_id,
        public_id=upload_res.get("public_id", public_id),
        asset_id=upload_res.get("asset_id"),
        resource_type="image",
        format=format_str,
        width=width,
        height=height,
        bytes=len(image_bytes),
        created_at=now_iso,
        status="uploaded",
        structure_type=structure_type,
        original_filename=getattr(target_file, "filename", None),
        preview_url=upload_res.get("preview_url")
        or cloudinary_service.build_preview_url(
            upload_res.get("public_id", public_id), format_str
        ),
        secure_url=upload_res.get("secure_url")
        or cloudinary_service.build_original_url(
            upload_res.get("public_id", public_id), format_str
        ),
    )

    # 6. Durably persist metadata in SQLite
    try:
        image_repository.save(metadata)
    except MetadataPersistenceError as e:
        # Partial failure handling: image was uploaded to Cloudinary, but DB write failed.
        logger.error(
            "Database persistence failed for image %s. Attempting Cloudinary rollback: %s",
            gen_image_id,
            e,
        )
        try:
            cloudinary_service.delete_image(metadata.public_id)
        except Exception as cleanup_err:
            logger.warning(
                "Rollback deletion in Cloudinary failed for %s: %s",
                metadata.public_id,
                cleanup_err,
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist image metadata. Upload rolled back.",
        )

    return metadata.to_upload_response()


@api_router.get(
    "/images/{image_id}",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Image Metadata",
    description="Retrieve stable metadata and delivery URLs for an uploaded inspection image.",
    tags=["Images"],
)
def get_image(image_id: str) -> ImageUploadResponse:
    """Retrieve image metadata by its application-level image identifier."""
    record = image_repository.get_by_id(image_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with id '{image_id}' not found.",
        )
    return record.to_upload_response()


@api_router.delete(
    "/images/{image_id}",
    response_model=ImageDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete Image Asset",
    description=(
        "Remove image from Cloudinary storage and delete associated durable metadata record. "
        "Handles partial failures explicitly."
    ),
    tags=["Images"],
)
def delete_image(image_id: str) -> ImageDeleteResponse:
    """Delete image asset from both Cloudinary and local metadata repository."""
    record = image_repository.get_by_id(image_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with id '{image_id}' not found.",
        )

    cloudinary_deleted = False
    metadata_deleted = False

    # Attempt Cloudinary deletion
    try:
        cloudinary_deleted = cloudinary_service.delete_image(record.public_id)
    except CloudinaryDeleteError as e:
        logger.error("Cloudinary deletion failed for %s: %s", record.public_id, e)
        cloudinary_deleted = False
    except CloudinaryConfigError:
        logger.warning(
            "Cloudinary credentials missing during deletion of %s.", record.public_id
        )
        cloudinary_deleted = False

    # Attempt database record deletion
    try:
        metadata_deleted = image_repository.delete(image_id)
    except MetadataPersistenceError as e:
        logger.error("Database deletion failed for %s: %s", image_id, e)
        metadata_deleted = False

    # Evaluate outcome and handle partial failures explicitly
    if not cloudinary_deleted and not metadata_deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete image from storage provider and metadata repository.",
        )
    if not cloudinary_deleted and metadata_deleted:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Partial deletion failure: database record removed, but Cloudinary asset could not be deleted.",
        )
    if cloudinary_deleted and not metadata_deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Partial deletion failure: Cloudinary asset removed, but database record could not be deleted.",
        )

    return ImageDeleteResponse(
        image_id=image_id,
        status="deleted",
        detail="Image asset deleted from Cloudinary and metadata repository.",
        cloudinary_deleted=True,
        metadata_deleted=True,
    )


@api_router.get(
    "/inspections/{inspection_id}/images",
    response_model=InspectionImagesListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Inspection Images",
    description="Retrieve all verified images registered to an inspection session.",
    tags=["Images"],
)
def list_inspection_images(inspection_id: str) -> InspectionImagesListResponse:
    """Retrieve all images associated with an inspection session."""
    records = image_repository.list_by_inspection_id(inspection_id)
    return InspectionImagesListResponse(
        inspection_id=inspection_id,
        total=len(records),
        images=[r.to_upload_response() for r in records],
    )

