"""Material Compatibility Subsystem for Jaldrishti Heritage Conservation.

Owner: Kirti Antil (IKS / Material Compatibility / Conservation Engineering Lead)
"""

from engineering.material_compatibility.dimensions import (
    COMPATIBILITY_WEIGHTS,
    RECOMMENDED_STANDARD_TESTS,
    compute_composite_compatibility,
)
from engineering.material_compatibility.engine import (
    MaterialCompatibilityEngine,
    MaterialCompatibilityError,
    default_engine,
    evaluate_compatibility,
)

__all__ = [
    "COMPATIBILITY_WEIGHTS",
    "RECOMMENDED_STANDARD_TESTS",
    "MaterialCompatibilityEngine",
    "MaterialCompatibilityError",
    "compute_composite_compatibility",
    "default_engine",
    "evaluate_compatibility",
]
