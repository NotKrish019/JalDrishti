# Jaldrishti Data Management & Storage Policy

---

## 1. Strict Dataset & Large File Policy
**WARNING: Do NOT commit raw imagery, large datasets, or annotations to Git.**

- **Darbhanga Fort Dataset:** The local Darbhanga Fort dataset must remain strictly local on the developer's machine under `data/raw/`.
- **Git Restrictions:**
  - `data/raw/*` is ignored by `.gitignore` (except `.gitkeep`).
  - `data/processed/*` is ignored by `.gitignore` (except `.gitkeep`).
  - `data/annotations/*` is ignored by `.gitignore` (except `.gitkeep`).
  - Large ML binaries, weights (`*.pt`, `*.onnx`), and point clouds are strictly ignored.

---

## 2. Directory Layout
```
data/
├── README.md
├── annotations/ # Ground truth annotation files (YOLO/COCO format - local only)
├── demo/        # Tiny, non-sensitive sample images (< 2MB) for demo runs
├── processed/   # Preprocessed, cropped, or normalized tiles (local only)
├── raw/         # Unmodified field survey photos (e.g. Darbhanga Fort - local only)
└── sample/      # Small reference images for smoke testing
```

---

## 3. Local Setup Instructions
To prepare local data for development:
1. Place raw field images into `data/raw/darbhanga_fort/`.
2. Do not run `git add` on raw image folders.
3. Verify that `git status` shows clean tracking via `.gitignore`.
