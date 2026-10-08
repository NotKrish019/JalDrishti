"""Comprehensive endpoint integration tests for JalDrishti Phase 2 APIs.

Tests:
- POST /vision/analyze
- POST /engineering
- POST /material-compatibility
- POST /restore
- POST /analyze
- GET /knowledge/structures
- GET /knowledge/structures/{id}
- GET /knowledge/sources
- Request validation, status codes, and contract conformance.
"""

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.analysis import AnalysisResult
from backend.app.schemas.engineering import EngineeringResult
from backend.app.schemas.material import MaterialCompatibilityResult
from backend.app.schemas.restoration import RestorationResult
from backend.app.schemas.vision import VisionResult
from backend.app.utils.contracts import validate_model_against_contract


client = TestClient(app)


# -----------------------------------------------------------------------------
# POST /vision/analyze Tests
# -----------------------------------------------------------------------------


def test_vision_analyze_default_request() -> None:
    """Verify POST /vision/analyze with minimal payload returns valid VisionResult."""
    payload = {
        "structure_type": "baoli",
        "name": "Agrasen ki Baoli",
        "region": "Delhi",
        "source_images": ["agrasen_01.jpg"],
    }
    response = client.post("/vision/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    model = VisionResult.model_validate(data)
    assert model.structure_type == "baoli"
    assert model.image_dimensions.width_pixels == 1920
    assert model.image_dimensions.height_pixels == 1080
    assert model.processing_metadata is not None
    assert model.processing_metadata.model_version is not None

    validate_model_against_contract(model, "vision_result.schema.json")


def test_vision_analyze_with_detections() -> None:
    """Verify POST /vision/analyze accepts and normalizes pre-detected defect segments."""
    payload = {
        "structure_type": "kund",
        "name": "Panna Meena ka Kund",
        "source_images": ["kund_01.jpg"],
        "image_dimensions": {"width_pixels": 2560, "height_pixels": 1440},
        "detections": [
            {
                "class_name": "crack",
                "confidence": 0.88,
                "bounding_box": [100.0, 200.0, 300.0, 400.0],
                "pixel_area": 1250.0,
                "coverage_ratio": 0.02,
                "component_count": 1,
                "total_length_pixels": 150.0,
                "largest_component_length_pixels": 150.0,
                "burden_score": 1.76,
            }
        ],
    }
    response = client.post("/vision/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    model = VisionResult.model_validate(data)
    assert len(model.detections) == 1
    assert model.detections[0].class_name == "crack"
    assert model.image_dimensions.width_pixels == 2560

    validate_model_against_contract(model, "vision_result.schema.json")


def test_vision_analyze_invalid_payload_fails() -> None:
    """Verify POST /vision/analyze with invalid confidence returns 422."""
    payload = {
        "structure_type": "baoli",
        "source_images": ["img.jpg"],
        "detections": [
            {
                "class_name": "crack",
                "confidence": 1.95,  # Invalid: > 1.0
                "bounding_box": [10.0, 20.0, 30.0, 40.0],
                "pixel_area": 100.0,
                "coverage_ratio": 0.01,
                "component_count": 1,
            }
        ],
    }
    response = client.post("/vision/analyze", json=payload)
    assert response.status_code == 422


# -----------------------------------------------------------------------------
# POST /engineering Tests
# -----------------------------------------------------------------------------


def test_engineering_assessment_with_clean_structure() -> None:
    """Verify POST /engineering on pristine structure yields high condition score."""
    payload = {
        "structure_type": "baoli",
        "image_dimensions": {"width_pixels": 1920, "height_pixels": 1080},
        "detections": [],
    }
    response = client.post("/engineering", json=payload)
    assert response.status_code == 200

    data = response.json()
    model = EngineeringResult.model_validate(data)
    assert model.visual_condition_score.value >= 90.0
    assert model.restoration_priority_score.value <= 40.0
    assert len(model.root_cause_analysis) >= 1
    assert "prototype" in model.engineering_disclaimer.lower()

    validate_model_against_contract(model, "engineering_result.schema.json")


def test_engineering_assessment_with_severe_defects() -> None:
    """Verify POST /engineering correctly degrades condition and raises priority on defects."""
    payload = {
        "vision": {
            "structure_type": "vav",
            "image_dimensions": {"width_pixels": 1920, "height_pixels": 1080},
            "detections": [
                {
                    "class_name": "vegetation_root_intrusion",
                    "confidence": 0.94,
                    "bounding_box": [200.0, 300.0, 800.0, 900.0],
                    "pixel_area": 45000.0,
                    "coverage_ratio": 0.08,
                    "component_count": 4,
                    "burden_score": 3.5,
                },
                {
                    "class_name": "crack",
                    "confidence": 0.91,
                    "bounding_box": [400.0, 500.0, 600.0, 700.0],
                    "pixel_area": 2500.0,
                    "coverage_ratio": 0.12,
                    "component_count": 2,
                    "burden_score": 2.2,
                },
            ],
        },
        "structure_name": "Rani ki Vav",
        "region": "Patan, Gujarat",
    }
    response = client.post("/engineering", json=payload)
    assert response.status_code == 200

    data = response.json()
    model = EngineeringResult.model_validate(data)
    # Deteriorated condition
    assert model.visual_condition_score.value < 85.0
    # Elevated restoration priority
    assert model.restoration_priority_score.value > 50.0
    # Root causes include vegetation wedging and settlement
    findings = [r.finding.lower() for r in model.root_cause_analysis]
    assert any("vegetat" in f or "root" in f for f in findings)
    assert any("fracture" in f or "crack" in f for f in findings)

    validate_model_against_contract(model, "engineering_result.schema.json")


def test_engineering_assessment_invalid_request_fails() -> None:
    """Verify POST /engineering returns 422 if required structure type missing."""
    payload = {
        "image_dimensions": {"width_pixels": 1920, "height_pixels": 1080},
        # Missing structure_type
    }
    response = client.post("/engineering", json=payload)
    assert response.status_code == 422


# -----------------------------------------------------------------------------
# POST /material-compatibility Tests
# -----------------------------------------------------------------------------


def test_material_compatibility_default_evaluation() -> None:
    """Verify POST /material-compatibility returns valid MaterialCompatibilityResult."""
    payload = {
        "original_material": "hydraulic_lime_mortar",
        "candidate_materials": ["surkhi_lime_mortar", "portland_cement_opc"],
        "original_material_confidence": 0.80,
    }
    response = client.post("/material-compatibility", json=payload)
    assert response.status_code == 200

    data = response.json()
    model = MaterialCompatibilityResult.model_validate(data)
    assert model.original_material == "hydraulic_lime_mortar"
    assert model.verification_required is True
    assert len(model.candidate_interventions) == 2

    # Surkhi lime mortar should be recommended; Portland cement prohibited
    surkhi = next(c for c in model.candidate_interventions if "surkhi" in c.intervention_material)
    opc = next(c for c in model.candidate_interventions if "cement" in c.intervention_material or "opc" in c.intervention_material)
    assert "recommended" in surkhi.recommendation.value
    assert opc.recommendation.value == "prohibited_incompatible"

    validate_model_against_contract(model, "material_compatibility.schema.json")


def test_material_compatibility_empty_payload() -> None:
    """Verify POST /material-compatibility with empty JSON defaults gracefully."""
    response = client.post("/material-compatibility", json={})
    assert response.status_code == 200

    data = response.json()
    model = MaterialCompatibilityResult.model_validate(data)
    assert model.verification_required is True
    assert len(model.candidate_interventions) >= 1
    validate_model_against_contract(model, "material_compatibility.schema.json")


# -----------------------------------------------------------------------------
# POST /restore Tests
# -----------------------------------------------------------------------------


def test_restoration_roadmap_endpoint() -> None:
    """Verify POST /restore returns phased conservation actions conforming to schema."""
    payload = {
        "structure_type": "baoli",
        "visual_condition_score": 50.0,
        "water_functionality_score": 45.0,
        "crack_burden": 0.15,
        "vegetation_burden": 0.18,
        "siltation_level": "moderate",
    }
    response = client.post("/restore", json=payload)
    assert response.status_code == 200

    data = response.json()
    model = RestorationResult.model_validate(data)
    assert len(model.prioritized_actions) >= 2
    assert len(model.incompatible_practices) >= 1
    assert model.iks_guidelines.traditional_mortar_recipe is not None

    validate_model_against_contract(model, "restoration_result.schema.json")


# -----------------------------------------------------------------------------
# POST /analyze (Unified Pipeline) Tests
# -----------------------------------------------------------------------------


def test_analyze_unified_pipeline_success() -> None:
    """Verify POST /analyze executes end-to-end and returns full AnalysisResult."""
    payload = {
        "structure_type": "baoli",
        "name": "Chand Baori",
        "region": "Abhaneri, Rajasthan",
        "source_images": ["chand_baori_main.jpg"],
        "detections": [
            {
                "class_name": "crack",
                "confidence": 0.89,
                "bounding_box": [150.0, 250.0, 350.0, 450.0],
                "pixel_area": 1200.0,
                "coverage_ratio": 0.015,
                "component_count": 1,
            }
        ],
    }
    response = client.post("/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    analysis = AnalysisResult.model_validate(data)

    assert analysis.project_version == "0.1.0"
    assert analysis.structure.type == "baoli"
    assert analysis.structure.name == "Chand Baori"
    assert analysis.metadata.pipeline_status == "completed"

    # Verify nested vision output
    assert len(analysis.vision.detections) == 1

    # Verify nested engineering scores
    assert analysis.visual_condition.value > 0.0
    assert analysis.water_functionality.value > 0.0

    # Verify material & restoration guidance
    assert analysis.material.verification_required is True
    assert len(analysis.restoration.prioritized_actions) >= 1

    # Strict JSON Schema validation against /contracts/analysis.schema.json
    validate_model_against_contract(analysis, "analysis.schema.json")


def test_analyze_empty_source_images_fails() -> None:
    """Verify POST /analyze rejects request with empty source_images list."""
    payload = {
        "structure_type": "baoli",
        "source_images": [],  # Violates min_length=1
    }
    response = client.post("/analyze", json=payload)
    assert response.status_code == 422


# -----------------------------------------------------------------------------
# GET /knowledge Tests
# -----------------------------------------------------------------------------


def test_get_known_structures() -> None:
    """Verify GET /knowledge/structures returns catalog of known typologies."""
    response = client.get("/knowledge/structures")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 4
    typologies = [s.get("id") for s in data]
    assert "baoli" in typologies
    assert "kund" in typologies


def test_get_structure_details() -> None:
    """Verify GET /knowledge/structures/{id} returns full typology record."""
    response = client.get("/knowledge/structures/baoli")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "baoli"
    assert "engineering_principles" in data


def test_get_structure_details_not_found() -> None:
    """Verify GET /knowledge/structures/invalid returns 404."""
    response = client.get("/knowledge/structures/non_existent_structure")
    assert response.status_code == 404


def test_get_literature_sources() -> None:
    """Verify GET /knowledge/sources returns bibliographic sources."""
    response = client.get("/knowledge/sources")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


# -----------------------------------------------------------------------------
# Multipart Upload & Vision Model Integration Tests
# -----------------------------------------------------------------------------


def test_analyze_multipart_image_upload() -> None:
    """Verify POST /analyze handles multipart/form-data with binary image file."""
    # Create minimal 1x1 GIF/PNG byte payload
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01\x00\x00\x00\x01\x00\x08\x06\x00\x00\x00\x5c\x72\xa8\x66\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"

    files = {
        "images": ("survey_wall.png", png_bytes, "image/png"),
    }
    data = {
        "structure_type": "baoli",
        "name": "Darbhanga Fort Baoli",
        "region": "Bihar, India",
        "notes": "Severe cracks on north retaining masonry wall",
        "roi_box": "[20, 30, 200, 150]",
    }

    response = client.post("/analyze", data=data, files=files)
    assert response.status_code == 200

    res = response.json()
    model = AnalysisResult.model_validate(res)
    assert model.structure.name == "Darbhanga Fort Baoli"
    assert model.structure.type == "baoli"
    assert len(model.vision.detections) >= 1
    assert model.vision.detections[0].class_name == "crack"
    assert model.visual_condition.value > 0.0

    validate_model_against_contract(model, "analysis.schema.json")


def test_analyze_with_krish_demo_asset() -> None:
    """Verify POST /analyze integrates Krish's pilot evaluation detections."""
    payload = {
        "structure_type": "baoli",
        "name": "Darbhanga Damaged Masonry",
        "source_images": ["crack_1.jpg"],
    }
    response = client.post("/analyze", json=payload)
    assert response.status_code == 200

    res = response.json()
    model = AnalysisResult.model_validate(res)
    assert len(model.vision.detections) >= 1
    # Check that crack from demo summary is detected
    crack_det = next((d for d in model.vision.detections if d.class_name == "crack"), None)
    assert crack_det is not None
    assert crack_det.confidence >= 0.70

    validate_model_against_contract(model, "analysis.schema.json")


def test_vision_analyze_multipart_upload() -> None:
    """Verify POST /vision/analyze handles multipart/form-data."""
    jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x11\x08\x00\x10\x00\x10\x03\x01\"\x00\x02\x11\x01\x03\x11\x01\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xbf\x00\xff\xd9"
    files = {
        "images": ("wall_fissure.jpg", jpeg_bytes, "image/jpeg"),
    }
    data = {
        "structure_type": "kund",
        "roi_box": "[10, 15, 80, 120]",
    }
    response = client.post("/vision/analyze", data=data, files=files)
    assert response.status_code == 200

    res = response.json()
    model = VisionResult.model_validate(res)
    assert model.structure_type == "kund"
    assert len(model.detections) >= 1
    validate_model_against_contract(model, "vision_result.schema.json")
