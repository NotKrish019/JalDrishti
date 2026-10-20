"""Smoke tests verifying the frontend project scaffold structure and configuration."""

import json
from pathlib import Path


def test_frontend_scaffold_files_exist() -> None:
    """Verify presence of key frontend configuration and entrypoint files."""
    frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"

    required_files = [
        "package.json",
        "package-lock.json",
        "tsconfig.json",
        "vite.config.ts",
        "index.html",
        "src/App.tsx",
        "src/main.tsx",
        "src/index.css",
        "src/services/api.ts",
        "src/types/index.ts",
    ]

    for rel_path in required_files:
        target = frontend_dir / rel_path
        assert target.exists(), f"Frontend scaffold missing required file: {rel_path}"


def test_frontend_package_json_validity() -> None:
    """Verify that frontend/package.json is valid JSON with expected scripts."""
    pkg_path = Path(__file__).resolve().parent.parent.parent / "frontend" / "package.json"
    with open(pkg_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("name") == "jaldrishti-frontend"
    assert "scripts" in data
    assert "dev" in data["scripts"]
    assert "build" in data["scripts"]
