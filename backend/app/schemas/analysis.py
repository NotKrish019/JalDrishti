"""Unified analysis contract schemas mirroring contracts/analysis.schema.json.

Maintained by Swastik Parmar (Backend / Integration Engineer).
Top-level pipeline contract connecting:
- Vision (Krish)
- Engineering & IKS (Kirti Antil)
- Backend Orchestration (Swastik Parmar)
- Frontend Visualization (Anika Jain)
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.engineering import EngineeringResult, ScoreMetric
from backend.app.schemas.material import MaterialCompatibilityResult
from backend.app.schemas.restoration import RestorationResult
from backend.app.schemas.vision import VisionResult


class PipelineStatus(str, Enum):
    """Pipeline execution status."""

    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class StructureTypeEnum(str, Enum):
    """Traditional water structure architectural classifications."""

    BAOLI = "baoli"
    BAWARI = "bawari"
    KUND = "kund"
    VAV = "vav"
    TANK = "tank"
    OTHER = "other"


class StructureInfo(BaseModel):
    """Contextual metadata regarding the target heritage water structure."""

    model_config = ConfigDict(extra="ignore")

    type: StructureTypeEnum = Field(..., description="Classification of water structure")
    name: Optional[str] = Field(default=None, description="Monument or site designation")
    region: Optional[str] = Field(default=None, description="Geographical or administrative location")
    source_images: List[str] = Field(
        ..., min_length=1, description="URIs or file references of inspected imagery"
    )


class AnalysisMetadata(BaseModel):
    """Metadata regarding analysis pipeline execution and provenance."""

    model_config = ConfigDict(extra="ignore")

    created_at: str = Field(..., description="ISO 8601 timestamp of analysis generation")
    pipeline_status: PipelineStatus = Field(
        ..., description="Execution status across pipeline components"
    )
    orchestrated_by: Optional[str] = Field(
        default="Swastik Parmar (Backend Orchestrator)",
        description="Module or agent responsible for orchestration",
    )


class AnalysisResult(BaseModel):
    """Unified top-level analysis contract."""

    model_config = ConfigDict(extra="ignore")

    project_version: str = Field(
        default="0.1.0",
        description="Schema and project contract version (strictly 0.1.0)",
    )
    structure: StructureInfo = Field(
        ..., description="Structure classification and source assets"
    )
    vision: Union[VisionResult, Dict[str, Any]] = Field(
        ..., description="Vision inference payload matching vision_result.schema.json"
    )
    visual_condition: Union[ScoreMetric, Dict[str, Any]] = Field(
        ..., description="Condition evaluation score matching engineering_result.schema.json"
    )
    water_functionality: Union[ScoreMetric, Dict[str, Any]] = Field(
        ..., description="Hydrological assessment matching engineering_result.schema.json"
    )
    material: Union[MaterialCompatibilityResult, Dict[str, Any]] = Field(
        ..., description="Material compatibility matching material_compatibility.schema.json"
    )
    root_cause: Dict[str, Any] = Field(
        ..., description="Deterministic root cause analysis identifying degradation mechanisms"
    )
    restoration: Union[RestorationResult, Dict[str, Any]] = Field(
        ..., description="Restoration roadmap matching restoration_result.schema.json"
    )
    metadata: AnalysisMetadata = Field(
        ..., description="Pipeline execution metadata and audit trail"
    )
