# Annotation plan

Status 2026-10-19: the supplied Darbhanga Fort dataset already has YOLO **crack** boxes (see
`DATASET_AUDIT.md`), which is what the detection pilot uses. What is still missing:

* **Label quality.** Boxes on photometric copies of the same photograph disagree in 223 groups,
  and some boxes are loose (whole mortar courses, window edges). A second-annotator review of the
  226 validation and 226 test photographs would make the reported metrics much more trustworthy.
* **Other conditions.** No labels exist for vegetation, material loss, open joints, staining or
  previous repairs; the model can only ever propose cracks.
* **Other structures and sites.** Everything is brick masonry from one fort.
* **Masks.** Crack length/width or area measurements need segmentation masks (Step 3).

The steps below cover a folder-labelled dataset (as in the earlier report) and the extensions
above.

## Step 1 — decide what folder labels mean (only for folder-labelled datasets)

1. Run the audit and contact sheets (see `DATASET_AUDIT.md`), 48+ images per folder.
2. For each folder, answer in writing:
   * Does every image show the condition, or only some?
   * Is it one condition (e.g. cracks) or several (cracks, vegetation, material loss, staining)?
   * What does `Background_images` / `ND` assert: no damage at all, or no target damage?
   * Are images crops of larger photographs (then related crops leak across splits)?
3. If the answer is "a defined, observable condition at image level", write it into
   `vision/configs/classification_pilot.yaml` → `labels.semantics`, rename the classes if
   needed (never `healthy` without justification), and set `labels.verified: true`.
4. Spot-check label noise: two reviewers independently label 200 random images per folder
   against the written definition; report agreement and disagreement rate. If disagreement is
   high, relabel before training.

## Step 2 — image-level review labels (improves the classifier)

Recommended multi-label image schema (one JSON object per image, stored in
`data/annotations/image_labels.jsonl`, gitignored):

```json
{"rel_path": "Damaged_images/0 (20).jpg",
 "conditions": ["crack", "open_joint"],
 "none_visible": false,
 "reviewer": "kirti", "reviewed_utc": "2026-10-20T10:00:00Z",
 "confidence": "certain", "notes": "",
 "structure_type": "fort_wall", "site_id": "darbhanga_fort", "capture_session": null}
```

Condition vocabulary (observable only): `crack`, `open_joint`, `material_loss`,
`vegetation`, `biological_growth`, `staining_or_efflorescence`, `previous_repair`, `other`.
`structure_type`, `site_id` and `capture_session` enable grouped splits and cross-site
evaluation later; leave them null rather than guessing.

## Step 3 — localisation (needed for any detector or mask claim)

* **Boxes** for a detector: CVAT or Label Studio, YOLO txt export; one class per condition
  above; minimum 300–400 images with at least one instance per class, plus images with none.
  Validate with a converter check (class ids, coordinates in [0, 1], no zero-area boxes).
* **Masks** for segmentation (crack width/length, area ratios): polygon or brush masks,
  exported as PNG with 0 = background. Thin cracks need consistent rules for line width.
* Hold out a test set annotated by a second person.

## Step 4 — broader water heritage

Add images from other sites and structure types (baoli, kund, tank, temple tank) with the
same schema, and evaluate per site and per structure type. A model trained only on Darbhanga
Fort must not be described as working on other structures until that evaluation exists.
