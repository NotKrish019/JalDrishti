# Jaldrishti Computer Vision Pipeline

**Owner:** Krish (Computer Vision / AI)  
**Status:** **PLANNED FUNCTIONALITY (Phase 1 Execution)**

---

## 1. Planned Pipeline Overview

The computer vision subsystem processes heritage survey images through a deterministic multi-stage computer vision workflow:

```
[Raw Input Image]
        │
        ▼
[1. Preprocessing Stage]
   - Radiometric & color contrast normalization (CLAHE)
   - High-resolution sliding window tiling (512x512 / 640x640 with overlap)
   - Perspective and aspect ratio preservation
        │
        ▼
[2. YOLOv8 Instance Segmentation]
   - Architecture: YOLOv8-seg fine-tuned on heritage masonry defects
   - Multi-class detection:
       • Cracks (shear, settlement, hairline)
       • Vegetation intrusion (deep root penetration & invasive ficus)
       • Stone spalling & delamination
       • Efflorescence & salt encrustation
       • Structural stone dislodgement
        │
        ▼
[3. Mask Generation & Re-stitching]
   - Output binary instance masks per defect instance
   - Non-Maximum Suppression (NMS) across tile boundaries
        │
        ▼
[4. OpenCV & scikit-image Morphological Analysis]
   - Connected component labeling
   - Skeletonization (Zhang-Suen / Lee's algorithm) for crack centerline extraction
   - Euclidean distance transform for crack path estimation
   - Boundary contour tracing & convex hull calculation
        │
        ▼
[5. Quantitative Image-Space Measurements]
   - Defect pixel area (`pixel_area`)
   - Region coverage ratio (`coverage_ratio` = defect pixels / total image pixels)
   - Contiguous component count (`component_count`)
   - Cumulative centerline pixel length (`total_length_pixels`)
   - Largest defect length (`largest_component_length_pixels`)
        │
        ▼
[6. Vision Result Payload]
   - Emits structured JSON strictly satisfying `contracts/vision_result.schema.json`
```

---

## 2. Measurement Boundary Note
- All Phase 1 measurements remain strictly in **relative/image-space (pixels & percentage coverage)** unless an explicit, calibrated physical metric reference (e.g. photogrammetric scale bar) is identified.
- Real-world millimeter measurements will not be guessed without geometric calibration.
