"""API router definition for BaoliGuard backend.

Maintained by Swastik Parmar (Backend / Integration Engineer).
Defines active Phase 1 endpoints and reserves future route contracts with 501 Not Implemented.
"""

from fastapi import APIRouter, HTTPException, status

from backend.app.schemas.health import HealthResponse

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
        project="baoliguard",
        version="0.1.0",
    )


# -----------------------------------------------------------------------------
# Reserved Future Pipeline Endpoints (Phase 2+)
# Explicitly return 501 Not Implemented to prevent fabricated mock responses.
# -----------------------------------------------------------------------------


@api_router.post(
    "/analyze",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Unified Analysis Pipeline (Reserved for Phase 2)",
    tags=["Pipeline"],
)
def analyze_structure() -> None:
    """Full end-to-end analysis pipeline orchestration.

    Reserved for Phase 2 orchestration across Vision, Engineering, IKS, and Restoration modules.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="POST /analyze is reserved for Phase 2 orchestration. Fabricated analysis results are strictly prohibited.",
    )


@api_router.post(
    "/engineering",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Engineering Assessment (Reserved for Phase 2)",
    tags=["Engineering"],
)
def assess_engineering() -> None:
    """Deterministic engineering condition scoring.

    Reserved for integration with Kirti Antil's engineering calculation module.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="POST /engineering is reserved for Phase 2 engineering rules integration.",
    )


@api_router.post(
    "/restore",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Restoration Roadmap (Reserved for Phase 2)",
    tags=["Restoration"],
)
def generate_restoration_roadmap() -> None:
    """Restoration planning and IKS intervention strategy.

    Reserved for Phase 2 conservation planning integration.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="POST /restore is reserved for Phase 2 restoration planning integration.",
    )


@api_router.post(
    "/material-compatibility",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Material Compatibility Evaluation (Reserved for Phase 2)",
    tags=["Materials"],
)
def evaluate_material_compatibility() -> None:
    """Material compatibility matrix evaluation.

    Reserved for Phase 2 material science integration.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="POST /material-compatibility is reserved for Phase 2 material evaluation integration.",
    )
