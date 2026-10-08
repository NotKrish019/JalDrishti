"""Restoration and IKS conservation guidance schemas.

Mirroring contracts/restoration_result.schema.json.
Maintained by Swastik Parmar (Backend / Integration Engineer).

Favors:
- MINIMUM INTERVENTION
- MATERIAL COMPATIBILITY
- PRESERVATION OF ORIGINAL FABRIC
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RestorationStrategy(str, Enum):
    """Overarching conservation strategy classification."""

    MINIMAL_STABILIZATION = "minimal_stabilization"
    MATERIAL_CONSOLIDATION = "material_consolidation"
    HYDROLOGICAL_REVIVAL = "hydrological_revival"
    COMPREHENSIVE_HERITAGE_REHABILITATION = "comprehensive_heritage_rehabilitation"


class ActionPhase(str, Enum):
    """Execution phases for sequenced conservation roadmap."""

    PHASE_1_IMMEDIATE_STABILIZATION = "phase_1_immediate_stabilization"
    PHASE_2_HYDROLOGICAL_REMEDIATION = "phase_2_hydrological_remediation"
    PHASE_3_MASONRY_AND_IKS_CONSOLIDATION = "phase_3_masonry_and_iks_consolidation"
    PHASE_4_LONG_TERM_MONITORING = "phase_4_long_term_monitoring"


class ActionUrgency(str, Enum):
    """Action intervention urgency."""

    IMMEDIATE = "immediate"
    HIGH = "high"
    MEDIUM = "medium"
    ROUTINE = "routine"


class IncompatibleSeverity(str, Enum):
    """Severity classification of destructive modern practices."""

    DESTRUCTIVE = "destructive"
    HIGH_RISK = "high_risk"
    MODERATE_RISK = "moderate_risk"


class PrioritizedAction(BaseModel):
    """Individual conservation task sequenced by dependency and urgency."""

    model_config = ConfigDict(extra="ignore")

    step: int = Field(..., ge=1, description="Sequence step index")
    phase: ActionPhase = Field(..., description="Roadmap execution phase")
    action_title: str = Field(..., description="Descriptive title of conservation intervention")
    target_defect: str = Field(..., description="Target degradation pattern addressed")
    recommended_technique: str = Field(..., description="Prescribed conservation methodology")
    material_specification: str = Field(
        ..., description="Compatible material formulation (e.g. lime:surkhi)"
    )
    urgency: ActionUrgency = Field(..., description="Intervention urgency")
    preconditions: Optional[List[str]] = Field(
        default=None, description="Prerequisite conditions before executing this action"
    )


class IncompatiblePractice(BaseModel):
    """Warning of modern practice known to cause accelerated decay on historic fabric."""

    model_config = ConfigDict(extra="ignore")

    prohibited_action: str = Field(..., description="Incompatible material or technique")
    failure_mechanism: str = Field(
        ..., description="Chemical/mechanical mechanism causing heritage damage"
    )
    severity: IncompatibleSeverity = Field(
        ..., description="Hazard level to historic structure"
    )


class IKSGuidelines(BaseModel):
    """Indigenous Knowledge Systems principles supporting restoration execution."""

    model_config = ConfigDict(extra="ignore")

    traditional_mortar_recipe: str = Field(
        ...,
        description="Traditional mortar blend (e.g. slaked fat lime + surkhi brick-dust + fermented organics)",
    )
    craftsmanship_references: List[str] = Field(
        default_factory=list,
        description="References to traditional treatises or regional guild practices",
    )
    seasonal_curing_rules: str = Field(
        ...,
        description="Traditional wet-jute curing and weather timing considerations",
    )


class RestorationResult(BaseModel):
    """Output contract for conservation intervention planning and restoration roadmaps."""

    model_config = ConfigDict(extra="ignore")

    restoration_strategy: RestorationStrategy = Field(
        ..., description="Primary conservation strategy"
    )
    prioritized_actions: List[PrioritizedAction] = Field(
        default_factory=list, description="Sequenced conservation actions"
    )
    incompatible_practices: List[IncompatiblePractice] = Field(
        default_factory=list, description="Strictly prohibited harmful interventions"
    )
    iks_guidelines: IKSGuidelines = Field(
        ..., description="Traditional knowledge guidelines and recipes"
    )

    # Optional top-level convenience fields supporting restoration contract specifications
    root_causes: Optional[List[str]] = Field(
        default=None, description="Summary of addressed root causes"
    )
    recommended_actions: Optional[List[str]] = Field(
        default=None, description="Summary list of recommended action titles"
    )
    priority: Optional[str] = Field(
        default=None, description="Overall restoration urgency tier"
    )
    warnings: List[str] = Field(
        default_factory=list, description="High-level restoration cautionary alerts"
    )
    verification_required: Optional[bool] = Field(
        default=None, description="Whether structural or chemical verification is required"
    )
