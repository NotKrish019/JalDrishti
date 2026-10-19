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
        "siteSpec.ts",
        "environment.ts",
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


def test_opening_frame_is_the_site_not_clouds() -> None:
    """The descent opens on the stepwell and its surroundings; the cloud prelude is gone."""
    scene = (SRC / "scene" / "DescentScene.ts").read_text(encoding="utf-8")
    atmosphere = (SRC / "scene" / "atmosphere.ts").read_text(encoding="utf-8")
    assert "buildEnvironment" in scene
    assert "createClouds" not in scene
    assert "createClouds" not in atmosphere


def test_poster_still_backs_loading_and_fallback() -> None:
    hero = (SRC / "components" / "HeroScene.tsx").read_text(encoding="utf-8")
    assert "/hero/opening.jpg" in hero
    assert (FRONTEND / "public" / "hero" / "opening.jpg").exists()


def test_narrative_and_method_sections_present() -> None:
    hero = (SRC / "components" / "HeroScene.tsx").read_text(encoding="utf-8")
    for label in ["01 / The place", "02 / The approach", "03 / The descent", "04 / The craft", "05 / The water", "06 / JalDrishti"]:
        assert label in hero, f"Missing descent chapter: {label}"
    home = "".join(p.read_text(encoding="utf-8") for p in (SRC / "components" / "home").glob("*.tsx"))
    for stage in ['label="See"', 'label="Understand"', 'label="Assess"', 'label="Revive"']:
        assert stage in home, f"Missing method section: {stage}"


def test_hero_leads_with_brand_and_broad_mission() -> None:
    """The first viewport names the brand and frames the stepwell as one example of a wider heritage."""
    hero = (SRC / "components" / "HeroScene.tsx").read_text(encoding="utf-8")
    assert "<h1" in hero and "JalDrishti" in hero
    assert "A deeper understanding of India&rsquo;s water heritage." in hero
    for form in ["stepwells", "kunds", "historic tanks"]:
        assert form in hero, f"Hero copy should name {form}"


def test_typology_scope_is_honest() -> None:
    """Forms without knowledge records must be labelled as scope, not as implemented coverage."""
    story = (SRC / "components" / "home" / "StorySections.tsx").read_text(encoding="utf-8")
    assert "Within the intended scope" in story
    assert "Knowledge records today" in story
    recorded = {p.stem for p in (FRONTEND.parent / "knowledge" / "structures").glob("*.json")} - {"index", "structure.schema"}
    for typology in recorded:
        assert typology in story.lower(), f"Recorded typology {typology} not acknowledged on the landing page"


def test_overlay_follows_camera_progress() -> None:
    """Chapter copy is driven by the scene's eased progress so it cannot drift from the camera."""
    scene = (SRC / "scene" / "DescentScene.ts").read_text(encoding="utf-8")
    hero = (SRC / "components" / "HeroScene.tsx").read_text(encoding="utf-8")
    assert "onProgress" in scene and "initialProgress" in scene
    assert "onProgress: (p) => overlayRef.current(p)" in hero


def test_reduced_motion_keeps_the_story() -> None:
    """Without the animated descent, the same chapters are rendered as a readable list."""
    hero = (SRC / "components" / "HeroScene.tsx").read_text(encoding="utf-8")
    assert 'id="descent-chapters"' in hero


def test_workspace_theme_is_scoped_to_internal_pages() -> None:
    """The internal-page theme lives under .ws (AppShell) and never reaches the landing page."""
    import re

    shell = (SRC / "components" / "AppShell.tsx").read_text(encoding="utf-8")
    assert 'className="ws ' in shell
    landing = (SRC / "pages" / "HomePage.tsx").read_text(encoding="utf-8")
    landing += (SRC / "components" / "HeroScene.tsx").read_text(encoding="utf-8")
    landing += "".join(p.read_text(encoding="utf-8") for p in (SRC / "components" / "home").glob("*.tsx"))
    classes = " ".join(re.findall(r'className=[{"`\'][^>]*', landing))
    used = re.findall(r"(?<![\w-])ws(?:-[a-z-]+)?(?![\w-])", classes)
    assert not used, f"landing must not use workspace theme classes: {sorted(set(used))}"
    assert "AppShell" not in (SRC / "pages" / "HomePage.tsx").read_text(encoding="utf-8")
    css = (SRC / "index.css").read_text(encoding="utf-8")
    assert ".ws {" in css and "@supports not ((backdrop-filter" in css and "@media print" in css


def test_inspect_page_is_one_workspace_without_step_cards() -> None:
    page = (SRC / "pages" / "UploadPage.tsx").read_text(encoding="utf-8")
    assert "Step 1" not in page and "Step 2" not in page and "<Card" not in page
    assert "Inspect a heritage water structure" in page


def test_reference_plates_are_unmodified_copies() -> None:
    """Pages use the supplied sample photographs byte-for-byte, never a re-encoded or edited copy."""
    import hashlib

    root = FRONTEND.parent
    pairs = {"sample4.jpeg": "stepwell-reflection.jpg", "sample0.jpeg": "well-octagon.jpg", "sample2.jpeg": "tank-mist.jpg"}
    for sample, plate in pairs.items():
        asset = FRONTEND / "public" / "plates" / plate
        assert asset.exists(), f"missing plate {plate}"
        original = root / sample
        if original.exists():
            assert hashlib.sha256(original.read_bytes()).digest() == hashlib.sha256(asset.read_bytes()).digest()
    container = (SRC / "components" / "PageContainer.tsx").read_text(encoding="utf-8")
    assert "reference photograph" in container
