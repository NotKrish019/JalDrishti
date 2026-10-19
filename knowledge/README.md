# JalDrishti Indian Knowledge Systems (IKS) & Conservation Knowledge Subsystem

**Lead:** Kirti Antil (IKS, Material Compatibility & Conservation Engineering Lead)  
**Team:** NeuralX  
**Subsystem Ownership:** `knowledge/`, `engineering/`, `tests/engineering/`  
**Status:** **PHASE 2 & PHASE 3 ENHANCED (Rigorous Traceability, Evidence Categorization & Conservation Ethics)**

---

## 1. Executive Summary & Vision

Traditional Indian water structures—**Baolis, Bawaris, Kunds, and Vavs**—represent sophisticated, microclimate-adapted hydraulic engineering monuments developed over more than a millennium. They capture monsoon runoff, moderate extreme diurnal heat, prevent siltation through staged gravity settling, and interact in hydrostatic equilibrium with unconfined aquifers without mechanical energy or fossil fuel.

JalDrishti’s knowledge subsystem provides a defensible, machine-readable, and peer-reviewable foundation for heritage conservation. It strictly avoids superficial or fabricated claims, ensuring that:
- Every substantive claim is anchored in authoritative bibliographic sources.
- Evidence types are rigorously categorized (historical practice, traditional recorded knowledge, modern conservation guidance, experimental findings, or unverified hypotheses).
- Geographic and geological limits of each practice are transparently documented.
- Traditional practices are never assumed to be universally applicable to every monument without considering local lithology, water chemistry, and environmental exposure.

---

## 2. Directory Layout & Organization

```
knowledge/
├── README.md                          # Primary knowledge architecture, review protocols, and extension guide
├── iks/
│   ├── README.md                      # Traditional hydrological tenets & environmental mechanics
│   └── hydrology_principles.json      # Traceable IKS principles with bibliographic citations & limitations
├── materials/
│   ├── README.md                      # Physical DNA, mineralogy, and breathability profiles
│   ├── material.schema.json           # JSON Schema validating material physical & chemical properties
│   ├── index.json                     # Registry of historic substrates and candidate mortars
│   ├── historic_sandstone.json        # Dholpur / Jodhpur historic sandstone substrate
│   ├── historic_quartzite.json        # Delhi quartzite rubblestone/ashlar substrate
│   ├── lakhori_brick.json             # Mughal / Sultanate thin lakhori terracotta brick
│   ├── hydraulic_lime_mortar.json     # Class A/B hydraulic lime bedding mortar
│   ├── surkhi_lime_mortar.json        # Traditional calcined clay pozzolana mortar blend
│   ├── fat_lime_putty.json            # Non-hydraulic Class C aged fat lime putty
│   ├── natural_hydraulic_lime_nhl.json# Standardized NHL 2 / NHL 3.5 mortar
│   ├── portland_cement_opc.json       # Incompatible modern Portland cement reference profile
│   └── generic_acrylic_filler.json    # Incompatible synthetic resin/epoxy reference profile
├── restoration/
│   └── README.md                      # Conservation ethics, ASI/INTACH guidelines & minimum intervention
├── sources/
│   ├── sources.schema.json            # JSON Schema enforcing academic and research provenance
│   └── sources_index.json             # Complete bibliographic repository with evidence types & limitations
└── structures/
    ├── structure.schema.json          # JSON Schema validating architectural typology knowledge entries
    ├── index.json                     # Master registry and lookup index for typologies
    ├── baoli.json                     # Deep engineering knowledge entry for Baoli
    ├── bawari.json                    # Deep engineering knowledge entry for Bawari
    ├── kund.json                      # Deep engineering knowledge entry for Kund
    └── vav.json                       # Deep engineering knowledge entry for Vav
```

---

## 3. Supported Water Structure Typologies

| Typology | Primary Regions | Hydrological Mechanism | Structural Innovation | Documented Limitations |
| :--- | :--- | :--- | :--- | :--- |
| **Baoli** | Indo-Gangetic Plains, Delhi NCR, UP, Haryana, MP, Northern Rajasthan | Deep unconfined aquifer abstraction with seasonal water table descent | Battered retaining walls with multi-tier vaulted struts and isolated potable well cylinder | Requires intact alluvial unconfined aquifer; regional water table depression below well bed terminates function. |
| **Bawari** | Arid Western India (Marwar, Mewar, Shekhawati, Malwa, Bundelkhand) | Dual-action micro-catchment runoff capture and fractured rock aquifer recharge | Steep-sided funnel revetment minimizing evaporative surface area; silt settling baffles | Catchment paving must not direct municipal sewage or agricultural pesticide runoff into recharge shaft. |
| **Kund** | Gujarat, Rajasthan, Braj / UP, Bihar, Bundelkhand, Varanasi | Dedicated surface rainwater harvesting into a perched freshwater retention basin | Symmetrical inverted stepped pyramid geometry; paved catchment apron (*paytan*) with multi-stage silt traps | Evaporation losses increase sharply if protective perimeter galleries or subterranean shading are damaged. |
| **Vav** | Gujarat (Patan, Ahmedabad, Adalaj, Modhera), SW Rajasthan | Monumental subterranean stepwell tapping deep alluvial sand aquifers | Colonnaded multi-storey pavilions (*kutas*) acting as horizontal struts against active lateral earth pressure; convective microclimatic cooling | Massive soil overburden requires balanced moisture; catastrophic dewatering can induce active earth thrust collapse. |

---

## 4. Evidence Classification & Source Recording Protocol

In accordance with conservation ethics, all substantive knowledge entries in `knowledge/sources/sources_index.json` must be categorized into one of five distinct evidence types:

1. **Documented Historical Practice (`documented_historical_practice`):**  
   Practices recorded in primary epigraphic records, historical chronicles, or original treatises (e.g., Shilpa Shastras, Manasara) or substantiated by archaeological excavation.
2. **Traditional Knowledge Recorded (`traditional_knowledge_recorded`):**  
   Living craft traditions or indigenous oral techniques recorded by reputable field researchers (e.g., Livingston, Jain-Neubauer, CSE Dying Wisdom).
3. **Modern Conservation Guidance (`modern_conservation_guidance`):**  
   Statutory conservation codes, standards, and manuals issued by recognized heritage authorities (e.g., ASI Conservation Manual 2020, INTACH Charter 2004, CPWD Heritage Handbook 2013, IS 712).
4. **Experimental Findings (`experimental_findings`):**  
   Peer-reviewed laboratory testing, empirical monitoring, or standardized material trials (e.g., RILEM TC 203-RHM, CGWB 2021 hydrogeological monitoring, IS 3115 pozzolanic reactivity).
5. **Unverified Claims or Hypotheses (`unverified_claim_hypothesis`):**  
   Folklore, anecdotal attributions, or untested hypotheses. These are marked explicitly with an evidence gap and MUST NOT be used to prescribe irreversible physical interventions.

### Required Fields for Knowledge Sources (`sources.schema.json`):
- `source_id`: Unique identifier (e.g. `SRC_ASI_CONSERVATION_MANUAL_2020`)
- `title`: Complete formal title
- `author`: Primary author, editor, or issuing committee
- `publisher`: Institutional publishing body
- `year`: Publication year or historical era
- `url`: Permanent web link or archive URL
- `topic`: Domain scope
- `evidence_type`: One of the 5 standardized evidence categories above
- `historical_period`: Historical epoch or statutory edition
- `relevant_region`: Geographic and geological boundaries of the evidence
- `applicable_structure_types`: Array of typologies where evidence is valid
- `confidence_limitations`: Explicit statement of data gaps, uncertainties, or sample boundaries
- `practical_conservation_relevance`: Direct application to field conservation
- `non_generalizable_conditions`: Specific environmental/structural scenarios where claim does NOT apply
- `expert_verification_status`: `"verified_authoritative"`, `"provisional_guidance"`, or `"needs_field_validation"`

---

## 5. Traceability of IKS Hydrological Principles

The indigenous hydrological principles cataloged in [`knowledge/iks/hydrology_principles.json`](file:///knowledge/iks/hydrology_principles.json) are directly tied to verified sources:

- **IKS_HYDRO_01 (Gradient-Driven Gravity Flow / Dhal-Yojana):**  
  *Sources:* `SRC_CSE_DYING_WISDOM_1997`, `SRC_LIVINGSTON_2002`  
  *Context:* Northwest arid zones. Relies on micro-catchment slopes and gravity head.  
  *Limitation:* Requires unobstructed topography; dense modern urban encroachments mandate engineered diversion channels.

- **IKS_HYDRO_02 (Subterranean Thermal Dampening / Bhugarbha Sheetalata):**  
  *Sources:* `SRC_LIVINGSTON_2002`, `SRC_JAIN_NEUBAUER_1981`  
  *Context:* Gujarat, Rajasthan, Delhi deep stepped trenches. Reduces summer evaporation up to 75%.  
  *Limitation:* Requires subterranean depth >8m; shallow tanks do not achieve significant thermal buffering.

- **IKS_HYDRO_03 (Multi-Stage Siltation Interception / Gadh-Niyantran):**  
  *Sources:* `SRC_CSE_DYING_WISDOM_1997`, `SRC_CGWB_TRADITIONAL_2021`  
  *Context:* Terraced silt settling sumps and carved gravel screens.  
  *Limitation:* Requires regular seasonal manual desiltation; unmaintained sumps choke and spill sediment into the well.

- **IKS_HYDRO_04 (Two-Way Aquifer Equilibrium / Jal-Samanvaya):**  
  *Sources:* `SRC_CGWB_TRADITIONAL_2021`, `SRC_UNESCO_RANI_KI_VAV_2014`  
  *Context:* Porous unmortared bedrock basements recharging unconfined aquifers.  
  *Limitation:* Cannot restore connectivity if regional over-extraction has dropped the water table far below the monument foundation.

- **IKS_HYDRO_05 (Functional Hydraulic Zoning / Pavitrata-Bhedana):**  
  *Sources:* `SRC_JAIN_NEUBAUER_1981`, `SRC_LIVINGSTON_2002`  
  *Context:* Physical separation of bathing stepped corridors from clean vertical well shafts.  
  *Limitation:* Cannot prevent contamination from airborne municipal waste without perimeter screening.

---

## 6. How to Add New Knowledge Entries & Validate

1. **Adding a New Source:**
   - Open [`knowledge/sources/sources_index.json`](file:///knowledge/sources/sources_index.json).
   - Add a new JSON object adhering strictly to [`knowledge/sources/sources.schema.json`](file:///knowledge/sources/sources.schema.json).
   - Ensure `evidence_type`, `non_generalizable_conditions`, and `confidence_limitations` are filled out. Do NOT invent references.

2. **Adding a New Material DNA Profile:**
   - Create `knowledge/materials/<material_id>.json` conforming to [`knowledge/materials/material.schema.json`](file:///knowledge/materials/material.schema.json).
   - Ensure all citations in `source_references` exist in `sources_index.json`.
   - Update `knowledge/materials/index.json`.

3. **Validation Command:**
   Run the automated repository test suite to verify schema compliance and citation integrity:
   ```bash
   ./.venv/bin/pytest tests/engineering/test_iks_knowledge.py -v
   ```
