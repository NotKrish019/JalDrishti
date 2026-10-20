# Jaldrishti Conservation Engineering Pipeline

**Owner:** Kirti Antil (IKS / Material Compatibility / Conservation Engineering)  
**Status:** **PLANNED SPECIFICATION (Phase 1 Execution)**

---

## 1. Planned Engineering Decision Flow

The engineering pipeline combines observational inputs with deterministic structural, hydrological, and conservation science rules:

```
[Vision Observations (Krish)]          [Inspection Observations (User Context)]
  • Defect coverage ratios               • Structure typology (Baoli/Kund/Vav)
  • Component counts                     • Regional geology & climate zone
  • Crack length & density               • Apparent water level & silt depth
             │                                        │
             └───────────────────┬────────────────────┘
                                 │
                                 ▼
                 [Deterministic Engineering Rules]
                 - Visual Condition Index calculation
                 - Water Functionality & Aquifer recharge index
                 - Masonry integrity penalty weighting
                                 │
                                 ▼
                [Root-Cause Analysis Deduction Trees]
                 - Matches defect combinations to structural/hydraulic faults:
                   * Basal spalling + damp line ──► Rising damp & blocked aquifer
                   * Linear shearing near steps ──► Foundation settlement
                   * Deep root expansion ─────────► Invasive woody species (Peepal/Banyan)
                                 │
                                 ▼
                [Material Compatibility Evaluation]
                 - Evaluates historical substrate (e.g. Dholpur sandstone + hydraulic lime)
                 - Compares candidate intervention mortars against 7 dimensions:
                   (Mechanical, Moisture, Thermal, Chemical, Reversibility, Heritage, Visual)
                 - Flags incompatible materials (OPC cement, epoxy resins)
                                 │
                                 ▼
                [Restoration Strategy & Roadmap Generation]
                 - Formulates 4-phase conservation roadmap:
                   Phase 1: Urgent physical stabilization & tree removal
                   Phase 2: Hydrological desiltation & runoff remediation
                   Phase 3: Traditional IKS lime repointing & stone consolidation
                   Phase 4: Community stewardship & cyclical monitoring
```

---

## 2. Fundamental Distinction: AI Inference vs. Deterministic Engineering

| Dimension | AI Inference Layer (Vision & Context) | Deterministic Engineering Engine |
| :--- | :--- | :--- |
| **Domain** | Visual perception & natural language contextualization | Structural degradation indices & conservation physics |
| **Input** | Raw photographs & bounding box proposals | Verified pixel metrics, material parameters, rule tables |
| **Method** | Neural network segmentation (YOLOv8) | Mathematical formulas & deterministic logic trees |
| **Output** | Detected defect contours & class probabilities | Bounded numerical scores (0-100) with confidence & limits |
| **Authority** | Observational hypothesis | Authoritative decision rule engine |

> [!CAUTION]
> Under no circumstances may an AI or LLM fabricate engineering scores, crack widths in millimeters, or approve structural safety. All scores are computed deterministically by the engineering engine.
