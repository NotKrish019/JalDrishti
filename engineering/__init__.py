"""Jaldrishti Conservation Engineering Subsystem.

Owner: Kirti Antil (IKS / Material Compatibility / Conservation Engineering Lead)

Provides deterministic condition assessment, water viability scoring, root-cause diagnosis,
material compatibility matrices, and phased restoration planning.
"""

from engineering.service import (
    ConservationEngineeringService,
    analyze_heritage_structure,
    default_service,
)
from engineering.knowledge_lookup import (
    KnowledgeRepository,
    get_structure,
    list_structures,
    get_source,
    default_repository,
)
from engineering.material_compatibility import (
    MaterialCompatibilityEngine,
    evaluate_compatibility,
    COMPATIBILITY_WEIGHTS,
)
from engineering.scoring import (
    VisualConditionScorer,
    calculate_visual_condition,
)
from engineering.water_functionality import (
    WaterFunctionalityScorer,
    calculate_water_functionality,
)
from engineering.root_cause import (
    RootCauseDeductionEngine,
    deduce_root_causes,
)
from engineering.restoration import (
    RestorationPlanningEngine,
    plan_restoration,
)
from engineering.assessment import (
    EngineeringAssessmentEngine,
    run_engineering_assessment,
    DEFAULT_ENGINEERING_DISCLAIMER,
)

__all__ = [
    # Top-Level Facade
    "ConservationEngineeringService",
    "analyze_heritage_structure",
    "default_service",
    # Knowledge Lookup
    "KnowledgeRepository",
    "get_structure",
    "list_structures",
    "get_source",
    "default_repository",
    # Material Compatibility
    "MaterialCompatibilityEngine",
    "evaluate_compatibility",
    "COMPATIBILITY_WEIGHTS",
    # Scoring & Indices
    "VisualConditionScorer",
    "calculate_visual_condition",
    "WaterFunctionalityScorer",
    "calculate_water_functionality",
    # Root Cause & Restoration
    "RootCauseDeductionEngine",
    "deduce_root_causes",
    "RestorationPlanningEngine",
    "plan_restoration",
    # Engineering Assessment
    "EngineeringAssessmentEngine",
    "run_engineering_assessment",
    "DEFAULT_ENGINEERING_DISCLAIMER",
]
