"""Static checks for the immersive landing experience and frontend honesty rules.

Owner: Anika Jain (Frontend)
"""

import json
import re
from pathlib import Path

FRONTEND = Path(__file__).resolve().parent.parent.parent / "frontend"
SRC = FRONTEND / "src"


def test_scene_modules_exist() -> None:
    """The 3D descent is split into focused, reusable modules."""
    for name in [
        "stepwellSpec.ts",
        "cameraPath.ts",
        "stepwell.ts",
        "atmosphere.ts",
        "water.ts",
        "materials.ts",
        "textures.ts",
        "quality.ts",
        "DescentScene.ts",
    ]:
        assert (SRC / "scene" / name).exists(), f"Missing scene module: {name}"


def test_scene_is_lazy_loaded() -> None:
    """three.js must not be imported eagerly by the application shell."""
    hero = (SRC / "components" / "HeroScene.tsx").read_text(encoding="utf-8")
    assert "import('../scene/DescentScene')" in hero
    assert not re.search(r"^import .* from 'three'", hero, re.MULTILINE)


def test_three_is_pinned() -> None:
    pkg = json.loads((FRONTEND / "package.json").read_text(encoding="utf-8"))
    version = pkg["dependencies"]["three"]
    assert re.fullmatch(r"\d+\.\d+\.\d+", version), f"three should be pinned exactly, got {version}"


def test_reduced_motion_and_webgl_fallbacks_present() -> None:
    hero = (SRC / "components" / "HeroScene.tsx").read_text(encoding="utf-8")
    assert "useReducedMotion" in hero
    assert "detectWebGL" in hero
    assert "'fallback'" in hero
    css = (SRC / "index.css").read_text(encoding="utf-8")
    assert "prefers-reduced-motion: reduce" in css


def test_no_cloudinary_secrets_in_frontend() -> None:
    for path in SRC.rglob("*.ts*"):
        text = path.read_text(encoding="utf-8")
        assert "CLOUDINARY_API_SECRET" not in text, f"Cloudinary secret referenced in {path}"
        assert "api_secret" not in text.lower(), f"Credential-like field in {path}"


def test_no_fabricated_marketing_statistics() -> None:
    """Previously shipped unverified figures must not return."""
    home = "".join(p.read_text(encoding="utf-8") for p in (SRC / "components" / "home").glob("*.tsx"))
    home += (SRC / "pages" / "HomePage.tsx").read_text(encoding="utf-8")
    for fabricated in ["3,000+", "0 kWh"]:
        assert fabricated not in home


def test_illustrative_model_is_disclosed() -> None:
    hero = (SRC / "components" / "HeroScene.tsx").read_text(encoding="utf-8")
    assert "Not a survey of a specific site" in hero
