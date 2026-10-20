# Jaldrishti Digital Twin Subsystem

**Owner:** Anika Jain (Frontend / PWA / Digital Twin)  
**Primary Ownership:**
- `/frontend`
- `/digital_twin`
- `/tests/frontend`

---

## 1. Overview
The Digital Twin module provides an interactive 3D spatial representation of heritage water structures:
- Loading lightweight 3D models (GLTF/GLB formats) of stepwells, tanks, and kunds.
- Projecting localized damage annotations and visual defects directly onto 3D coordinates.
- Simulating before/after conservation interventions (e.g., vegetation removal, desilted water tables, traditional lime repointing).
- Powering the in-browser viewer using Three.js / React Three Fiber.

---

## 2. Directory Layout
```
digital_twin/
├── README.md
├── metadata/  # Spatial coordinate mappings & defect anchor metadata
├── models/    # GLTF/GLB 3D assets (large raw scans kept out of Git)
├── textures/  # Material maps and surface texture representations
└── viewer/    # Three.js integration components and viewport handlers
```

---

## 3. Phase 0 Rule
No massive multi-gigabyte photogrammetry point clouds or heavy textures should be checked into Git. Use lightweight sample assets in Phase 1.
