"""Smoke test verifying basic Python imports and project modules."""

import sys


def test_python_version() -> None:
    """Verify that Python version meets >= 3.10 requirement."""
    assert sys.version_info >= (3, 10), "Python 3.10 or higher is required"


def test_core_dependencies_importable() -> None:
    """Verify that essential Phase 0 dependencies can be imported cleanly."""
    import fastapi
    import pydantic
    import uvicorn
    import jsonschema

    import importlib.metadata

    assert fastapi.__version__ is not None
    assert pydantic.__version__ is not None
    assert uvicorn.__version__ is not None
    assert importlib.metadata.version("jsonschema") is not None


def test_backend_app_importable() -> None:
    """Verify that backend application package imports without circular errors."""
    from backend.app.main import app

    assert app.title == "JalDrishti API"
