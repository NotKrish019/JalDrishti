"""Automated test suite for JalDrishti image upload, Cloudinary integration, and persistence.

Maintained by Swastik Parmar (Backend / Integration Engineer).
Tests:
1. Successful upload with mocked Cloudinary response and contract validation.
2. Empty file rejection (HTTP 400).
3. Unsupported format rejection (HTTP 400).
4. Oversized upload rejection with bounded stream handling (HTTP 413).
5. Corrupted image rejection (HTTP 400).
6. Missing Cloudinary configuration (HTTP 503).
7. Cloudinary service provider failure (HTTP 502).
8. Metadata persistence failure and Cloudinary rollback (HTTP 500).
9. Response schema conformance with contracts/image_upload_result.schema.json.
10. Safe error handling (no secrets or internal credentials leaked).
11. Image retrieval (GET /images/{id}) and 404 behavior.
12. Deletion workflow (DELETE /images/{id}) with complete and partial-failure handling.
13. Inspection association listing (GET /inspections/{id}/images).
14. Integration of image_id with POST /analyze pipeline.
"""

import io
from typing import Any, Dict
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from PIL import Image
import pytest

from backend.app.core.config import settings
from backend.app.db.image_repository import MetadataPersistenceError, image_repository
from backend.app.main import app
from backend.app.schemas.image import (
    ImageDeleteResponse,
    ImageUploadResponse,
    InspectionImagesListResponse,
)
from backend.app.utils.contracts import validate_model_against_contract

client = TestClient(app)


def create_sample_image(
    format_name: str = "JPEG", width: int = 120, height: int = 120, color: str = "blue"
) -> bytes:
    """Generate in-memory valid decoded image bytes for test isolation."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format=format_name)
    return buf.getvalue()


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch: pytest.MonkeyPatch):
    """Ensure mock Cloudinary environment variables and in-memory clean database."""
    monkeypatch.setattr(settings, "cloudinary_cloud_name", "test-cloud")
    monkeypatch.setattr(settings, "cloudinary_api_key", "test-api-key")
    monkeypatch.setattr(settings, "cloudinary_api_secret", "test-api-secret")
    monkeypatch.setattr(settings, "max_upload_size_bytes", 10 * 1024 * 1024)
    image_repository.clear()
    yield
    image_repository.clear()


def mock_cloudinary_upload_success(
    public_id: str = "jaldrishti/inspections/img_sample",
    format_str: str = "jpeg",
    width: int = 120,
    height: int = 120,
) -> Dict[str, Any]:
    """Helper mock dictionary simulating a successful Cloudinary SDK response."""
    return {
        "public_id": public_id,
        "asset_id": "mock_asset_id_999",
        "format": format_str,
        "resource_type": "image",
        "width": width,
        "height": height,
        "bytes": 2048,
        "created_at": "2026-10-19T07:15:00Z",
        "secure_url": f"https://res.cloudinary.com/test-cloud/image/upload/v1/{public_id}.{format_str}",
        "url": f"http://res.cloudinary.com/test-cloud/image/upload/v1/{public_id}.{format_str}",
    }


# -----------------------------------------------------------------------------
# 1. Successful Upload & Contract Validation
# -----------------------------------------------------------------------------


def test_successful_image_upload_with_mocked_cloudinary():
    """Verify successful upload flow, metadata storage, and contract schema compliance."""
    img_bytes = create_sample_image(format_name="JPEG", width=640, height=480)

    with patch(
        "cloudinary.uploader.upload",
        return_value=mock_cloudinary_upload_success(
            public_id="jaldrishti/inspections/img_test1",
            format_str="jpeg",
            width=640,
            height=480,
        ),
    ):
        response = client.post(
            "/images/upload",
            files={"file": ("test_baoli.jpg", img_bytes, "image/jpeg")},
            data={
                "inspection_id": "insp_delhi_001",
                "structure_type": "baoli",
                "structure_name": "Agrasen ki Baoli",
            },
        )

    assert response.status_code == 201
    data = response.json()

    # Verify model validation and contract adherence
    model = ImageUploadResponse.model_validate(data)
    assert model.format == "jpeg"
    assert model.width == 640
    assert model.height == 480
    assert model.inspection_id == "insp_delhi_001"
    assert "c_limit,w_800" in model.preview_url
    assert model.original_url is not None
    assert "test-api-secret" not in response.text

    # Verify shared JSON Schema validation against /contracts
    validate_model_against_contract(model, "image_upload_result.schema.json")

    # Verify durable persistence in SQLite
    stored = image_repository.get_by_id(model.image_id)
    assert stored is not None
    assert stored.inspection_id == "insp_delhi_001"
    assert stored.structure_type == "baoli"
    assert stored.original_filename == "test_baoli.jpg"


def test_successful_image_upload_with_images_field_name():
    """Verify frontend compatibility when payload uses 'images' multipart field."""
    img_bytes = create_sample_image(format_name="PNG", width=300, height=200)

    with patch(
        "cloudinary.uploader.upload",
        return_value=mock_cloudinary_upload_success(
            public_id="jaldrishti/inspections/img_test_png",
            format_str="png",
            width=300,
            height=200,
        ),
    ):
        response = client.post(
            "/images/upload",
            files={"images": ("survey_field.png", img_bytes, "image/png")},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["format"] == "png"
    assert data["width"] == 300
    assert data["height"] == 200
    assert data["inspection_id"] is not None


# -----------------------------------------------------------------------------
# 2-5. Input Rejection & Validation Tests
# -----------------------------------------------------------------------------


def test_empty_file_rejection():
    """Verify 0-byte file uploads are rejected with HTTP 400."""
    response = client.post(
        "/images/upload",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_missing_file_rejection():
    """Verify requests with no file attachment return HTTP 400."""
    response = client.post("/images/upload", data={"inspection_id": "insp_none"})
    assert response.status_code == 400
    assert "No image file provided" in response.json()["detail"]


def test_unsupported_format_rejection():
    """Verify non-whitelisted image formats (e.g. GIF, SVG, text) return HTTP 400."""
    # Create valid GIF bytes
    img = Image.new("RGB", (50, 50), color="green")
    buf = io.BytesIO()
    img.save(buf, format="GIF")
    gif_bytes = buf.getvalue()

    response = client.post(
        "/images/upload",
        files={"file": ("animation.gif", gif_bytes, "image/gif")},
    )
    assert response.status_code == 400
    assert "Unsupported image format" in response.json()["detail"]


def test_oversized_upload_rejection(monkeypatch: pytest.MonkeyPatch):
    """Verify uploads exceeding configured maximum size return HTTP 413 without memory exhaustion."""
    # Restrict max size to 256 bytes for testing
    monkeypatch.setattr(settings, "max_upload_size_bytes", 256)
    img_bytes = create_sample_image(width=100, height=100)
    assert len(img_bytes) > 256

    response = client.post(
        "/images/upload",
        files={"file": ("large.jpg", img_bytes, "image/jpeg")},
    )
    assert response.status_code == 413
    assert "exceeds maximum allowed limit" in response.json()["detail"]


def test_corrupted_image_rejection():
    """Verify byte streams with fake headers or corrupt contents return HTTP 400."""
    # JPEG SOI marker followed by garbage payload
    corrupted_bytes = b"\xff\xd8\xff\xe0" + b"not-a-valid-jpeg-image-payload" * 20

    response = client.post(
        "/images/upload",
        files={"file": ("corrupt.jpg", corrupted_bytes, "image/jpeg")},
    )
    assert response.status_code == 400
    assert "Corrupted or undecodable" in response.json()["detail"]


# -----------------------------------------------------------------------------
# 6-8. Cloudinary Provider & Persistence Failures
# -----------------------------------------------------------------------------


def test_missing_cloudinary_configuration(monkeypatch: pytest.MonkeyPatch):
    """Verify service returns HTTP 503 when Cloudinary credentials are missing."""
    monkeypatch.setattr(settings, "cloudinary_cloud_name", None)
    img_bytes = create_sample_image()

    response = client.post(
        "/images/upload",
        files={"file": ("valid.jpg", img_bytes, "image/jpeg")},
    )
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"].lower()


def test_cloudinary_service_failure():
    """Verify provider exceptions are caught and surfaced as HTTP 502 without leaking secrets."""
    img_bytes = create_sample_image()

    with patch("cloudinary.uploader.upload", side_effect=Exception("Gateway Timeout on Cloudinary")):
        response = client.post(
            "/images/upload",
            files={"file": ("valid.jpg", img_bytes, "image/jpeg")},
        )

    assert response.status_code == 502
    assert "Cloudinary image upload failed" in response.json()["detail"]
    assert "test-api-secret" not in response.text


def test_metadata_persistence_failure_triggers_cloudinary_rollback():
    """Verify metadata persistence error rolls back uploaded Cloudinary asset and returns HTTP 500."""
    img_bytes = create_sample_image()

    mock_destroy = MagicMock(return_value={"result": "ok"})

    with patch(
        "cloudinary.uploader.upload",
        return_value=mock_cloudinary_upload_success(public_id="jaldrishti/inspections/orphan_test"),
    ), patch(
        "cloudinary.uploader.destroy",
        mock_destroy,
    ), patch.object(
        image_repository,
        "save",
        side_effect=MetadataPersistenceError("Database disk failure"),
    ):
        response = client.post(
            "/images/upload",
            files={"file": ("valid.jpg", img_bytes, "image/jpeg")},
        )

    assert response.status_code == 500
    assert "Failed to persist image metadata. Upload rolled back." in response.json()["detail"]
    # Ensure rollback deletion was invoked
    mock_destroy.assert_called_once()


# -----------------------------------------------------------------------------
# 9-11. Image Retrieval, Listing, & Deletion
# -----------------------------------------------------------------------------


def test_get_image_metadata_and_404():
    """Verify GET /images/{image_id} returns metadata and handles non-existent IDs."""
    img_bytes = create_sample_image()

    with patch(
        "cloudinary.uploader.upload",
        return_value=mock_cloudinary_upload_success(public_id="jaldrishti/inspections/img_get_test"),
    ):
        upload_resp = client.post(
            "/images/upload",
            files={"file": ("monument.jpg", img_bytes, "image/jpeg")},
            data={"inspection_id": "insp_get_123"},
        )
    assert upload_resp.status_code == 201
    image_id = upload_resp.json()["image_id"]

    # Query existing image
    get_resp = client.get(f"/images/{image_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["image_id"] == image_id
    assert get_resp.json()["inspection_id"] == "insp_get_123"

    # Query non-existent image
    not_found = client.get("/images/img_non_existent_9999")
    assert not_found.status_code == 404


def test_list_inspection_images():
    """Verify GET /inspections/{inspection_id}/images lists all associated photos."""
    img_bytes = create_sample_image()

    with patch(
        "cloudinary.uploader.upload",
        return_value=mock_cloudinary_upload_success(public_id="jaldrishti/inspections/img_batch"),
    ):
        client.post(
            "/images/upload",
            files={"file": ("img1.jpg", img_bytes, "image/jpeg")},
            data={"inspection_id": "insp_batch_session"},
        )
        client.post(
            "/images/upload",
            files={"file": ("img2.jpg", img_bytes, "image/jpeg")},
            data={"inspection_id": "insp_batch_session"},
        )

    list_resp = client.get("/inspections/insp_batch_session/images")
    assert list_resp.status_code == 200
    list_model = InspectionImagesListResponse.model_validate(list_resp.json())
    assert list_model.total == 2
    assert len(list_model.images) == 2


def test_delete_image_success():
    """Verify complete image deletion from Cloudinary and database."""
    img_bytes = create_sample_image()

    with patch(
        "cloudinary.uploader.upload",
        return_value=mock_cloudinary_upload_success(public_id="jaldrishti/inspections/to_delete"),
    ):
        upload_resp = client.post(
            "/images/upload",
            files={"file": ("delete_me.jpg", img_bytes, "image/jpeg")},
        )
    image_id = upload_resp.json()["image_id"]

    with patch("cloudinary.uploader.destroy", return_value={"result": "ok"}):
        del_resp = client.delete(f"/images/{image_id}")

    assert del_resp.status_code == 200
    del_data = ImageDeleteResponse.model_validate(del_resp.json())
    assert del_data.status == "deleted"
    assert del_data.cloudinary_deleted is True
    assert del_data.metadata_deleted is True

    # Confirm it no longer exists in repository
    assert image_repository.get_by_id(image_id) is None


def test_delete_image_partial_failure_cloudinary():
    """Verify explicit error handling when Cloudinary deletion fails."""
    img_bytes = create_sample_image()

    with patch(
        "cloudinary.uploader.upload",
        return_value=mock_cloudinary_upload_success(public_id="jaldrishti/inspections/to_fail_del"),
    ):
        upload_resp = client.post(
            "/images/upload",
            files={"file": ("fail_del.jpg", img_bytes, "image/jpeg")},
        )
    image_id = upload_resp.json()["image_id"]

    with patch("cloudinary.uploader.destroy", side_effect=Exception("Cloudinary API unavailable")):
        del_resp = client.delete(f"/images/{image_id}")

    # Database deleted, Cloudinary failed -> HTTP 502
    assert del_resp.status_code == 502
    assert "Partial deletion failure" in del_resp.json()["detail"]


# -----------------------------------------------------------------------------
# 12. Integration with POST /analyze
# -----------------------------------------------------------------------------


def test_analyze_endpoint_integrates_with_image_id():
    """Verify POST /analyze resolves image reference and dimensions via registered image_id."""
    img_bytes = create_sample_image(width=1600, height=1200)

    with patch(
        "cloudinary.uploader.upload",
        return_value=mock_cloudinary_upload_success(
            public_id="jaldrishti/inspections/img_integrated",
            width=1600,
            height=1200,
        ),
    ):
        upload_resp = client.post(
            "/images/upload",
            files={"file": ("agrasen_wall.jpg", img_bytes, "image/jpeg")},
            data={"structure_type": "baoli", "structure_name": "Agrasen ki Baoli"},
        )
    assert upload_resp.status_code == 201
    image_id = upload_resp.json()["image_id"]

    # Now submit inspection analysis referencing this image_id
    analyze_payload = {
        "image_id": image_id,
        "structure_type": "baoli",
        "name": "Agrasen ki Baoli",
        "region": "Delhi",
    }
    analyze_resp = client.post("/analyze", json=analyze_payload)
    assert analyze_resp.status_code == 200

    analysis_data = analyze_resp.json()
    assert analysis_data["structure"]["name"] == "Agrasen ki Baoli"
    # Source image was automatically resolved to the Cloudinary preview URL
    assert "c_limit,w_800" in analysis_data["structure"]["source_images"][0]
    # Spatial dimensions were automatically resolved from image record
    assert analysis_data["vision"]["image_dimensions"]["width_pixels"] == 1600
    assert analysis_data["vision"]["image_dimensions"]["height_pixels"] == 1200
