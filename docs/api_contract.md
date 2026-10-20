# Jaldrishti API Contract & Orchestration Protocol

**Status:** Phase 0 Specification  
**Primary Implementers (Phase 1):** Swastik Parmar (Backend) & Anika Jain (Frontend)

---

## 1. High-Level Communication Flow

During full system execution in Phase 1, the orchestration pipeline executes as follows:

```
[Frontend Client]
       │
       │  POST /analyze  (Multipart form: image file(s) + structure metadata)
       ▼
[Backend FastAPI Orchestrator]
       │
       ├────►  1. Invoke Vision Pipeline (Krish)
       │          - Passes input image bytes
       │          - Receives VisionResult (masks, defect bboxes, pixel metrics)
       │          - Validates against contracts/vision_result.schema.json
       │
       ├────►  2. Invoke Engineering Assessment (Kirti Antil)
       │          - Passes vision defect metrics + structural typology
       │          - Calculates visual_condition_score & water_functionality_score
       │          - Traces root-cause failure mechanisms
       │          - Validates against contracts/engineering_result.schema.json
       │
       ├────►  3. Query IKS & Material Knowledge (Kirti Antil)
       │          - Evaluates substrate compatibility against candidate repairs
       │          - Validates against contracts/material_compatibility.schema.json
       │
       ├────►  4. Generate Restoration Plan (Kirti Antil & Swastik Parmar)
       │          - Assembles prioritized multi-phase conservation strategy
       │          - Validates against contracts/restoration_result.schema.json
       │
       ▼
[Backend Assembles Unified AnalysisResult]
       │  (Conforms strictly to contracts/analysis.schema.json)
       │
       ▼
[Frontend Client Renders Results]
       - Overlays defect contours on 2D image
       - Renders score gauges & IKS cards
       - Projects damage onto 3D Digital Twin model
```

---

## 2. API Endpoints Overview

### `GET /health` (Implemented in Phase 0)
Returns server status and project version.
- **Response:**
  ```json
  {
    "status": "ok",
    "project": "jaldrishti",
    "version": "0.1.0"
  }
  ```

### `POST /analyze` (Planned for Phase 1)
Primary analysis ingestion endpoint.
- **Request:** `multipart/form-data`
  - `images`: List of image files (JPEG, PNG).
  - `structure_type`: String (e.g. `baoli`, `kund`, `vav`, `bawari`).
  - `region`: Optional geographic string (e.g. `Bihar`, `Rajasthan`, `Gujarat`).
- **Response:** HTTP 200 with JSON payload conforming to [`/contracts/analysis.schema.json`](file:///contracts/analysis.schema.json).

> [!NOTE]
> `POST /analyze` is intentionally **NOT** implemented in Phase 0. No mocked or hallucinated data is served until live pipeline integration in Phase 1.
