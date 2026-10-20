# JalDrishti

**Jal-Dharohar Digital Intelligence &amp; Conservation Platform**  
*An AI-assisted digital engineering and heritage conservation system for traditional Indian water infrastructure.*

---

## 🏛️ Vision
BaoliGuard bridges traditional Indian hydraulic wisdom with cutting-edge digital engineering to safeguard and revitalize India's historic stepwells, kunds, bawaris, and tanks. Through a sovereign, India-first architecture, the platform empowers conservation architects, researchers, and administrators to make evidence-based, material-compatible conservation decisions.

---

## 🌊 The Problem
Traditional Indian water structures encapsulate centuries of hydrological and architectural mastery. However, these structures suffer from severe physical degradation (vegetation intrusion, masonry cracking, siltation) and are frequently damaged further by incompatible modern repairs (e.g., non-breathable Portland cement). Furthermore, traditional construction wisdom and regional material knowledge are fragmented, and no non-invasive digital diagnostic system currently exists to support their systematic revival.

---

## 🔄 Core Philosophy: SEE → UNDERSTAND → ASSESS → REVIVE

```
    SEE           ──►  Computer Vision: Non-invasive visual defect detection & quantification
    UNDERSTAND    ──►  Indian Knowledge Systems (IKS): Material DNA & historical context
    ASSESS        ──►  Engineering Rules: Deterministic condition & water functionality scoring
    REVIVE        ──►  Conservation Engine: Phased, material-compatible restoration planning
```

---

## 🏗️ Architecture

```
                       +-----------------------------+
                       |        Frontend PWA         |
                       |    (React / TypeScript)     |
                       +--------------+--------------+
                                      │
                                      ▼
                       +-----------------------------+
                       |       FastAPI Backend       |
                       |   (System Orchestrator)     |
                       +--------------+--------------+
                                      │
                 ┌────────────────────┼────────────────────┐
                 ▼                    ▼                    ▼
        +------------------+ +------------------+ +------------------+
        |  Vision (SEE)    | | Engineering/IKS  | | Digital Twin     |
        |  YOLOv8 + OpenCV | | (ASSESS/UNDERSTAND| | Three.js (3D)   |
        +------------------+ +------------------+ +------------------+
```

Inter-subsystem communication is strictly governed by standardized JSON schemas located in [`/contracts`](file:///contracts).

---

## 💻 Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend & PWA** | React 18, Vite, TypeScript, Tailwind CSS, Three.js |
| **Backend & Integration** | Python 3.10+, FastAPI, Pydantic, Uvicorn, Cloudinary, SQLite |
| **Computer Vision & AI** | PyTorch, Ultralytics YOLOv8 segmentation, OpenCV, NumPy, scikit-image |
| **Conservation Engineering** | Python, deterministic physics & condition scoring formulas |
| **Knowledge Engine** | Indian Knowledge Systems (IKS) ontology, JSON schemas |
| **Sovereign AI** | Local-first, India-first inference architecture (pre-aligned with BharatGen/Param) |

---

## 👥 Team & Ownership Boundaries

| Teammate | Role | Primary Directories |
| :--- | :--- | :--- |
| **Krish** | Computer Vision / AI Lead | [`/vision`](file:///vision), [`/scripts/vision`](file:///scripts/vision), [`/vision/tests`](file:///vision/tests) |
| **Kirti Antil** | IKS, Materials & Conservation Engineering Lead | [`/knowledge`](file:///knowledge), [`/engineering`](file:///engineering), [`/tests/engineering`](file:///tests/engineering) |
| **Anika Jain** | Frontend, PWA & Digital Twin Lead | [`/frontend`](file:///frontend), [`/digital_twin`](file:///digital_twin), [`/tests/frontend`](file:///tests/frontend) |
| **Swastik Parmar** | Backend, Integration & System Orchestration Lead | [`/backend`](file:///backend), [`/integration`](file:///integration), [`/tests/backend`](file:///tests/backend), [`/tests/integration`](file:///tests/integration) |

---

## 📌 Current Status

**PHASE 0 — REPOSITORY BOOTSTRAP**

This repository is currently in **Phase 0**. In accordance with hackathon setup guidelines:
- Repository architecture, directory ownership, and contracts have been initialized.
- Base FastAPI `/health` endpoint and smoke tests are verified.
- **NO production features, model weights, large datasets, or fabricated outputs have been committed.**

---

## ⚠️ Important Dataset & Large File Policy
Large field datasets (e.g., Darbhanga Fort imagery) and machine learning model weights (`*.pt`, `*.onnx`, `*.safetensors`, `*.bin`) are **intentionally excluded from Git** via [`.gitignore`](file:///.gitignore). Developers maintain raw data locally in `data/raw/`.

---

## ⚖️ Disclaimer
BaoliGuard is a prototype decision-support and conservation assistance system. It is **not** a certified structural engineering, archaeological, or official conservation assessment tool. All calculations and recommendations provide preliminary guidance and must be validated through authorized on-site multidisciplinary heritage audits.
