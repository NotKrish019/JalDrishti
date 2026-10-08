"""Engineering and deterministic condition scoring schemas.

Mirroring contracts/engineering_result.schema.json.
Maintained by Swastik Parmar (Backend / Integration Engineer).

IMPORTANT:
These metrics are prototype decision-support / triage scores.
They are NOT certified structural safety assessments and must never be represented as such.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DeductionUrgency(str, Enum):
    """Urgency level assigned to a root cause deduction finding."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ScoreMetric(BaseModel):
    """Standardized metric representation for deterministic assessments."""

    model_config = ConfigDict(extra="ignore")

    value: float = Field(..., description="Calculated score value")
    scale_min: float = Field(..., description="Minimum scale boundary (typically 0.0)")
    scale_max: float = Field(..., description="Maximum scale boundary (typically 100.0 or 1.0)")
    method: str = Field(..., description="Deterministic calculation rule or formula identifier")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence based on coverage and input quality"
    )
    limitations: List[str] = Field(
        ..., min_length=1, description="Explicit limitations and assumptions of calculation"
    )


class SubScores(BaseModel):
    """Specific dimensional sub-scores for structural and hydrological evaluation."""

    model_config = ConfigDict(extra="ignore")

    vegetation_intrusion_index: Optional[ScoreMetric] = Field(
        default=None, description="Index of invasive root penetration and biomass impact"
    )
    masonry_integrity_index: Optional[ScoreMetric] = Field(
        default=None, description="Index of stone/joint condition and spalling load"
    )
    siltation_obstruction_index: Optional[ScoreMetric] = Field(
        default=None, description="Index of hydraulic inlet/catchment blockage"
    )


class RootCauseDeduction(BaseModel):
    """Rule deduction linking observable defects to failure mechanisms."""

    model_config = ConfigDict(extra="ignore")

    finding: str = Field(..., description="Observable defect or empirical condition")
    probable_cause: str = Field(..., description="Inferred mechanism causing the degradation")
    evidence_rules: List[str] = Field(
        default_factory=list, description="Identifiers of rule criteria that triggered deduction"
    )
    urgency: Optional[DeductionUrgency] = Field(
        default=None, description="Urgency priority of finding"
    )


class EngineeringResult(BaseModel):
    """Output contract for deterministic engineering assessment."""

    model_config = ConfigDict(extra="ignore")

    visual_condition_score: ScoreMetric = Field(
        ..., description="Deterministic condition index from visual defects"
    )
    water_functionality_score: ScoreMetric = Field(
        ..., description="Hydrological viability and catchment continuity assessment"
    )
    restoration_priority_score: ScoreMetric = Field(
        ..., description="Action priority score synthesizing condition and revival potential"
    )
    engineering_disclaimer: str = Field(
        default="Outputs represent non-invasive prototype decision-support metrics and cannot replace on-site certified structural/geotechnical audits.",
        description="Mandatory disclaimer stating outputs are non-invasive prototype scores.",
    )
    sub_scores: Optional[SubScores] = Field(
        default=None, description="Detailed dimensional sub-scores"
    )
    root_cause_analysis: Optional[List[RootCauseDeduction]] = Field(
        default=None, description="Deterministic root cause rule deductions"
    )
