"""Frontend component and scaffold tests for Phase 1 (PWA Foundation + Design System).

Owner: Anika Jain (Frontend / PWA / Digital Twin)
"""

import json
from pathlib import Path


def test_reusable_components_exist() -> None:
    """Verify presence of all required Phase 1 reusable UI components."""
    frontend_src = Path(__file__).resolve().parent.parent.parent / "frontend" / "src"
    components_dir = frontend_src / "components"

    required_components = [
        "Header.tsx",
        "Navigation.tsx",
        "PageContainer.tsx",
        "Section.tsx",
        "Button.tsx",
        "Card.tsx",
        "StatusBadge.tsx",
        "ScoreCard.tsx",
        "EmptyState.tsx",
        "LoadingState.tsx",
        "UploadZone.tsx",
        "HeroScene.tsx",
        "JalDrishtiLogo.tsx",
    ]

    for comp in required_components:
        target = components_dir / comp
        assert target.exists(), f"Missing required reusable component: {comp}"


def test_page_routes_exist() -> None:
    """Verify presence of all required Phase 1 page views."""
    frontend_src = Path(__file__).resolve().parent.parent.parent / "frontend" / "src"
    pages_dir = frontend_src / "pages"

    required_pages = [
        "HomePage.tsx",
        "UploadPage.tsx",
        "AnalysisPage.tsx",
        "ReportPage.tsx",
    ]

    for page in required_pages:
        target = pages_dir / page
        assert target.exists(), f"Missing required page view: {page}"


def test_pwa_manifest_validity() -> None:
    """Verify that frontend/public/manifest.json is well-formed PWA manifest."""
    manifest_path = Path(__file__).resolve().parent.parent.parent / "frontend" / "public" / "manifest.json"
    assert manifest_path.exists(), "PWA manifest.json must exist in public/"

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("short_name") in ["JalDrishti", "Jaldrishti"]
    assert "start_url" in data
    assert data.get("display") == "standalone"


def test_api_service_and_mock_fixtures_exist() -> None:
    """Verify presence of API service abstraction, types, and mock fixtures."""
    frontend_src = Path(__file__).resolve().parent.parent.parent / "frontend" / "src"

    assert (frontend_src / "services" / "api.ts").exists(), "services/api.ts must exist"
    assert (frontend_src / "types" / "index.ts").exists(), "types/index.ts must exist"
    assert (frontend_src / "mocks" / "fixtures.ts").exists(), "mocks/fixtures.ts must exist"


def test_phase2_inspection_components_exist() -> None:
    """Verify presence of Phase 2 inspection, ROI selection, and visualization components."""
    frontend_src = Path(__file__).resolve().parent.parent.parent / "frontend" / "src"
    components_dir = frontend_src / "components"

    phase2_components = [
        "InspectionCanvas.tsx",
        "ROISelector.tsx",
        "DefectLegend.tsx",
        "VisualMetricsPanel.tsx",
    ]

    for comp in phase2_components:
        target = components_dir / comp
        assert target.exists(), f"Missing required Phase 2 component: {comp}"

    sample_asset = Path(__file__).resolve().parent.parent.parent / "frontend" / "public" / "samples" / "stepwell_ashlar_wall.svg"
    assert sample_asset.exists(), "Sample stepwell SVG asset must exist in public/samples/"


def test_phase3_iks_material_restoration_components_exist() -> None:
    """Verify presence of Phase 3 IKS, Material DNA, and Restoration components."""
    frontend_src = Path(__file__).resolve().parent.parent.parent / "frontend" / "src"
    components_dir = frontend_src / "components"

    phase3_components = [
        "ConservationChain.tsx",
        "MaterialDnaCard.tsx",
        "WhyThisRecommendation.tsx",
        "RootCauseAnalysisCard.tsx",
        "RestorationRoadmap.tsx",
    ]

    for comp in phase3_components:
        target = components_dir / comp
        assert target.exists(), f"Missing required Phase 3 component: {comp}"


