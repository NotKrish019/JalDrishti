# Jaldrishti System Architecture

**Project:** Jaldrishti — Jal-Dharohar Digital Intelligence & Conservation Platform  
**System Paradigm:** Sovereign AI, Indigenous Knowledge Systems (IKS) & Deterministic Conservation Engineering

---

## 1. High-Level Pipeline Flow

```
                      +-----------------------------+
                      |        Frontend PWA         |
                      |   (React / TypeScript / UI) |
                      +--------------+--------------+
                                     |
                                     | HTTP POST /analyze
                                     v
                      +-----------------------------+
                      |       FastAPI Backend       |
                      |   (Orchestrator - Swastik)  |
                      +--------------+--------------+
                                     |
                                     v
        +-------------------------------------------------------+
        |                  SEE: Vision Subsystem                 |
        |             (Krish: YOLOv8 + OpenCV/skimage)          |
        | - Classifies structure typology                       |
        | - Segments visible cracks, vegetation, spalling       |
        | - Measures relative pixel areas, lengths, components  |
        +----------------------------+--------------------------+
                                     |
                                     | vision_result.schema.json
                                     v
        +-------------------------------------------------------+
        |                 ASSESS: Engineering Rules             |
        |              (Kirti Antil: Deterministic Rules)       |
        | - Calculates visual condition index                   |
        | - Computes water functionality & siltation index      |
        | - Formulates root-cause failure hypotheses            |
        +----------------------------+--------------------------+
                                     |
                                     v
        +-------------------------------------------------------+
        |          UNDERSTAND: IKS & Material Knowledge         |
        |               (Kirti Antil: Knowledge Engine)         |
        | - Retrieves regional indigenous hydrological wisdom   |
        | - Evaluates multi-dimensional material compatibility  |
        | - Recommends traditional lime / herbal recipes        |
        +----------------------------+--------------------------+
                                     |
                                     v
        +-------------------------------------------------------+
        |               REVIVE: Restoration Engine              |
        |           (Kirti Antil & Swastik Parmar)              |
        | - Formulates phased, prioritized interventions        |
        | - Explicitly flags destructive modern interventions   |
        | - Emits restoration roadmap adhering to contracts     |
        +----------------------------+--------------------------+
                                     |
                                     | analysis.schema.json
                                     v
                      +-----------------------------+
                      |       FastAPI Backend       |
                      |   (Validates & Assembles)   |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |    Frontend & Digital Twin   |
                      |  (Anika: 2D Dashboards +    |
                      |   3D Three.js Visualizer)   |
                      +-----------------------------+
```

---

## 2. Clear Responsibility Boundaries

Each module answers an exact, scoped question without trespassing on other modules:

| Subsystem | Core Question Answered | Authority & Boundaries |
| :--- | :--- | :--- |
| **Vision (Krish)** | *"What is visibly present?"* | Purely observational. Computes bounding boxes, masks, component counts, and image-space pixel metrics. Does **not** invent real-world millimeters or judge structural safety. |
| **Engineering (Kirti)** | *"What can we quantitatively infer using defined rules?"* | Deterministic formulas. Calculates condition, functionality, and priority scores. Enforces explicit limitation metadata on every calculation. |
| **IKS (Kirti)** | *"What indigenous knowledge is relevant?"* | Curates historical regional water management wisdom and traditional craftsmanship principles, backed by traceable citations. |
| **Material (Kirti)** | *"What intervention families may be compatible?"* | Evaluates compatibility dimensions (mechanical, moisture, thermal, chemical, reversibility, heritage, visual). Treats photo-identification as probabilistic. |
| **Restoration (Kirti & Swastik)** | *"What action should be considered?"* | Constructs phased remediation roadmaps while warning against damaging modern materials (e.g., OPC cement rendering). |
| **AI / Contextualization** | *"How can the system explain and contextualize the result?"* | Generates human-readable explanations strictly grounded in structured vision and engineering findings. **Never** invents measurements or bypasses engineering calculations. |
| **Frontend (Anika)** | *"How should the user interact with the system?"* | Presentation layer. Displays images, defect overlays, scores, IKS wisdom, and interactive 3D digital twins. Never implements isolated business scoring. |
| **Backend (Swastik)** | *"How do all modules communicate?"* | Central hub. Orchestrates pipeline execution, validates schemas, and guarantees API reliability. |

---

## 3. Sovereign AI & Local Capability
- **India-First Architecture:** The core prototype runs fully locally on developer workstations without hard dependencies on proprietary external cloud LLMs.
- **National AI Alignment:** Prepared to interface with sovereign compute infrastructures (such as BharatGen / Param models) in future phases.
- **Safety Boundary:** The system strictly separates AI perceptual/explanatory capabilities from deterministic engineering and material rules.
