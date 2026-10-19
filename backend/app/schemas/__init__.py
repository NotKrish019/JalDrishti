"""Pydantic schemas mirroring /contracts for backend validation.

Maintained by Swastik Parmar (Backend / Integration Engineer).
Phase 1 Foundation: Establishes strong typed boundaries for all cross-module data models.
"""

from backend.app.schemas.analysis import (
    AnalysisMetadata,
    AnalysisResult,
    PipelineStatus,
    StructureInfo,
    StructureTypeEnum,
)
from backend.app.schemas.engineering import (
    DeductionUrgency,
    EngineeringResult,
    RootCauseDeduction,
    ScoreMetric,
    SubScores,
)
from backend.app.schemas.health import HealthResponse
from backend.app.schemas.image import (
    ImageDeleteResponse,
    ImageMetadata,
    ImageUploadResponse,
    InspectionImagesListResponse,
)
from backend.app.schemas.requests import (
    AnalysisPipelineRequest,
    EngineeringAssessmentRequest,
    MaterialCompatibilityRequest,
    RestorationPlanRequest,
)
from backend.app.schemas.material import (
    CandidateIntervention,
    CompatibilityDimensions,
    CompatibilityRecommendation,
    MaterialCompatibilityResult,
)
from backend.app.schemas.restoration import (
    ActionPhase,
    ActionUrgency,
    IKSGuidelines,
    IncompatiblePractice,
    IncompatibleSeverity,
    PrioritizedAction,
    RestorationResult,
    RestorationStrategy,
)
from backend.app.schemas.vision import (
    DetectionItem,
    ImageDimensions,
    ProcessingMetadata,
    RelativeSeverity,
    ScaleReference,
    StructureType,
    VisionDefectClass,
    VisionResult,
)

__all__ = [
    # Health & Requests
    "HealthResponse",
    "EngineeringAssessmentRequest",
    "MaterialCompatibilityRequest",
    "RestorationPlanRequest",
    "AnalysisPipelineRequest",
    # Vision
    "StructureType",
    "VisionDefectClass",
    "RelativeSeverity",
    "ImageDimensions",
    "ScaleReference",
    "DetectionItem",
    "ProcessingMetadata",
    "VisionResult",
    # Engineering
    "DeductionUrgency",
    "ScoreMetric",
    "SubScores",
    "RootCauseDeduction",
    "EngineeringResult",
    # Material
    "CompatibilityRecommendation",
    "CompatibilityDimensions",
    "CandidateIntervention",
    "MaterialCompatibilityResult",
    # Restoration
    "RestorationStrategy",
    "ActionPhase",
    "ActionUrgency",
    "IncompatibleSeverity",
    "PrioritizedAction",
    "IncompatiblePractice",
    "IKSGuidelines",
    "RestorationResult",
    # Top-level Analysis
    "PipelineStatus",
    "StructureTypeEnum",
    "StructureInfo",
    "AnalysisMetadata",
    "AnalysisResult",
    # Images & Inspection Ingestion
    "ImageUploadResponse",
    "ImageMetadata",
    "ImageDeleteResponse",
    "InspectionImagesListResponse",
]

