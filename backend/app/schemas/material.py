"""Material compatibility assessment schemas.

Mirroring contracts/material_compatibility.schema.json.
Maintained by Swastik Parmar (Backend / Integration Engineer).

Material identification from photography is inherently probabilistic.
Laboratory characterization is required prior to irreversible physical intervention.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CompatibilityRecommendation(str, Enum):
    """Conservation intervention decision classification."""

    STRONGLY_RECOMMENDED = "strongly_recommended"
    RECOMMENDED = "recommended"
    ACCEPTABLE_CONDITIONAL = "acceptable_conditional"
    PROHIBITED_INCOMPATIBLE = "prohibited_incompatible"


class CompatibilityDimensions(BaseModel):
    """Multi-dimensional evaluation matrix for conservation materials (0.0 - 10.0 scale)."""

    model_config = ConfigDict(extra="ignore")

    mechanical: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Elastic modulus matching, compressive strength compatibility (avoiding over-strength)",
    )
    moisture: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Breathability, vapor permeability, capillarity matching",
    )
    thermal: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Thermal expansion coefficient compatibility",
    )
    chemical: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Chemical inertness, absence of deleterious salts",
    )
    reversibility: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Degree to which intervention can be removed without damaging original fabric",
    )
    heritage: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Alignment with traditional IKS construction methods and authentic regional recipes",
    )
    visual: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Texture, color, and aging compatibility with surrounding historic masonry",
    )


class CandidateIntervention(BaseModel):
    """Evaluated intervention option against historic substrate."""

    model_config = ConfigDict(extra="ignore")

    intervention_material: str = Field(
        ..., description="Candidate mortar, grout, or conservation consolidant"
    )
    compatibility_score: float = Field(
        ..., ge=0.0, le=100.0, description="Composite compatibility score (0-100)"
    )
    compatibility_dimensions: CompatibilityDimensions = Field(
        ..., description="7-dimension evaluation matrix"
    )
    recommendation: CompatibilityRecommendation = Field(
        ..., description="Conservation decision classification"
    )
    warnings: List[str] = Field(
        default_factory=list, description="Critical alerts regarding degradation risks"
    )


class MaterialCompatibilityResult(BaseModel):
    """Output contract for material compatibility evaluation."""

    model_config = ConfigDict(extra="ignore")

    original_material: str = Field(
        ..., description="Identified or inferred original historic substrate"
    )
    original_material_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence of photographic/contextual identification (probabilistic)",
    )
    verification_required: bool = Field(
        ...,
        description="Mandatory flag indicating if lab characterization is required before physical work",
    )
    recommended_tests: Optional[List[str]] = Field(
        default=None, description="Recommended on-site or lab testing procedures"
    )
    candidate_interventions: List[CandidateIntervention] = Field(
        default_factory=list, description="Evaluated candidate conservation materials"
    )

    # Optional top-level convenience summary fields
    compatibility_score: Optional[float] = Field(
        default=None, ge=0.0, le=100.0, description="Overall selected compatibility score"
    )
    compatibility_dimensions: Optional[CompatibilityDimensions] = Field(
        default=None, description="Selected compatibility dimensional scores"
    )
    recommendation: Optional[CompatibilityRecommendation] = Field(
        default=None, description="Overall conservation recommendation"
    )
    warnings: List[str] = Field(
        default_factory=list, description="Top-level conservation warnings"
    )
