# Jaldrishti Shared Contracts

**Status:** Phase 0 Locked & Shared  
**Audience:** All Teammates (Krish, Kirti, Anika, Swastik)

---

## 1. Purpose of Shared Contracts
To eliminate integration friction and allow parallel engineering without merge conflicts, all inter-module communication is governed by the JSON schemas in this directory.

```
       [Vision Pipeline - Krish]
                   │
                   ▼ (vision_result.schema.json)
[Backend Orchestrator - Swastik] ◄──► [Engineering / IKS - Kirti]
                   │                   (engineering_result.schema.json)
                   │                   (material_compatibility.schema.json)
                   │                   (restoration_result.schema.json)
                   ▼ (analysis.schema.json)
     [Frontend & PWA - Anika]
```

---

## 2. Included Schema Contracts
1. **[`analysis.schema.json`](file:///contracts/analysis.schema.json)**  
   Top-level unified schema returned by the backend `POST /analyze` pipeline and consumed by the frontend.
2. **[`vision_result.schema.json`](file:///contracts/vision_result.schema.json)**  
   Schema representing computer vision defect segments (cracks, vegetation, spalling, masonry dislodgement). All measurements are in relative/image-space pixels.
3. **[`engineering_result.schema.json`](file:///contracts/engineering_result.schema.json)**  
   Schema for deterministic engineering scores (`visual_condition_score`, `water_functionality_score`, `restoration_priority_score`). Enforces explicit limitations and methodology metadata to prevent confusing prototype scores with certified audits.
4. **[`material_compatibility.schema.json`](file:///contracts/material_compatibility.schema.json)**  
   Multi-dimensional evaluation matrix (mechanical, moisture, thermal, chemical, reversibility, heritage, visual) comparing candidate interventions against historical substrates.
5. **[`restoration_result.schema.json`](file:///contracts/restoration_result.schema.json)**  
   Phased restoration roadmap incorporating indigenous knowledge systems (IKS) and highlighting incompatible modern practices (e.g. Portland cement rendering).
6. **[`image_upload_result.schema.json`](file:///contracts/image_upload_result.schema.json)**  
   Shared contract for image ingestion, Cloudinary storage, responsive preview generation, and original image retrieval connecting Anika (Frontend) and Krish (Vision) via backend orchestration.


---

## 3. Modification Rule
Files in `/contracts` are **shared/controlled**. No individual teammate should modify these schemas unilaterally without team consensus.
