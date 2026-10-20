# Jaldrishti Team Ownership & Directory Boundaries

**Project:** Jaldrishti — Jal-Dharohar Digital Intelligence & Conservation Platform  
**Phase:** Phase 0 (Bootstrap & Governance)

---

## 1. Ownership Principle
To ensure frictionless parallel engineering and eliminate merge conflicts during hackathon execution, each teammate has **strict and exclusive ownership** of specific directories.

Code additions must occur inside the respective teammate's domain. Shared files must NOT be casually altered without explicit consensus.

---

## 2. Teammate Allocation

### 👤 Krish — Computer Vision / AI Lead
- **Primary Ownership:**
  - [`/vision`](file:///vision)
  - [`/scripts/vision`](file:///scripts/vision)
  - [`/vision/tests`](file:///vision/tests)
- **Responsibilities in Future Phases:**
  - Dataset preparation and local split inspection (Darbhanga Fort imagery).
  - YOLOv8 segmentation model configuration and fine-tuning.
  - Model evaluation, validation, and inference optimization.
  - Image preprocessing (tiling, resizing, radiometric normalization).
  - Instance segmentation masks (cracks, vegetation root intrusion, stone spalling, biological growth).
  - OpenCV and scikit-image post-processing (skeletonization, connected components).
  - Visual defect quantification (pixel area, coverage ratio, crack length metrics).
  - Emitting payloads adhering strictly to [`/contracts/vision_result.schema.json`](file:///contracts/vision_result.schema.json).

---

### 👤 Kirti Antil — IKS, Materials & Conservation Engineering Lead
- **Primary Ownership:**
  - [`/knowledge`](file:///knowledge)
  - [`/engineering`](file:///engineering)
  - [`/tests/engineering`](file:///tests/engineering) (and `/engineering/tests`)
- **Responsibilities in Future Phases:**
  - Indian Knowledge Systems (IKS) hydrological principles and typology curation.
  - Traditional water system wisdom across Baolis, Kunds, Vavs, and Bawaris.
  - Traditional construction practices and historical material knowledge (lime DNA, hydraulic mortars, surkhi, herbal additives).
  - Multi-dimensional material compatibility matrix logic (mechanical, moisture, thermal, chemical, reversibility, heritage, visual).
  - Deterministic condition scoring formulas (`visual_condition_score`, `water_functionality_score`, `restoration_priority_score`).
  - Root-cause deduction trees connecting visible damage symptoms to hydrological failure.
  - Research traceability catalog maintaining credible academic and archaeological citations in `knowledge/sources/`.
  - Emitting payloads adhering strictly to [`/contracts/engineering_result.schema.json`](file:///contracts/engineering_result.schema.json) and [`/contracts/material_compatibility.schema.json`](file:///contracts/material_compatibility.schema.json).

---

### 👤 Anika Jain — Frontend, PWA & Digital Twin Lead
- **Primary Ownership:**
  - [`/frontend`](file:///frontend)
  - [`/digital_twin`](file:///digital_twin)
  - [`/tests/frontend`](file:///tests/frontend)
- **Responsibilities in Future Phases:**
  - React + Vite + TypeScript PWA user interface and styling with Tailwind CSS.
  - Heritage survey image upload workflows and interactive inspection views.
  - Dynamic defect overlays and bounding box/mask projection on 2D imagery.
  - Score dashboards visualizing engineering condition, water viability, and urgency.
  - IKS contextual wisdom presentation and material compatibility displays.
  - Phased restoration roadmap visualizer with "before vs. after" restoration simulations.
  - Three.js Digital Twin 3D spatial viewer (`/digital_twin`) loading GLTF/GLB models and anchoring defect markers.
  - Consuming payloads adhering to [`/contracts/analysis.schema.json`](file:///contracts/analysis.schema.json).

---

### 👤 Swastik Parmar — Backend, Integration & System Orchestrator Lead
- **Primary Ownership:**
  - [`/backend`](file:///backend)
  - [`/integration`](file:///integration)
  - [`/tests/backend`](file:///tests/backend)
  - [`/tests/integration`](file:///tests/integration)
- **Responsibilities in Future Phases:**
  - FastAPI application architecture, routing, and lifecycle management.
  - System orchestration invoking Vision, Engineering, and IKS modules in sequence.
  - Request/response validation against shared schemas via Pydantic.
  - API gateway endpoints (e.g., `POST /analyze`, `GET /health`).
  - Cross-module integration tests and golden sample test fixtures (`/integration`).
  - Assembling unified `AnalysisResult` responses for the frontend.
  - Demo reliability, execution performance, and local development harness.

---

## 3. Shared and Controlled Files
The following files and folders require team consensus and caution before editing:
- [`/contracts`](file:///contracts) (JSON Schema specifications)
- [`/docs`](file:///docs) (System documentation and guidelines)
- [`/.github`](file:///.github) (PR and issue workflows)
- [`README.md`](file:///README.md)
- [`.gitignore`](file:///.gitignore)
- [`.gitattributes`](file:///.gitattributes)
- [`.env.example`](file:///.env.example)
- [`requirements.txt`](file:///requirements.txt)
- [`pyproject.toml`](file:///pyproject.toml)
