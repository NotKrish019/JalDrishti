# Model card — image-level deterioration classifier (pilot)

**Status: not trained.** Training is blocked until the folder labels are reviewed and
`labels.verified` is set in `vision/configs/classification_pilot.yaml`. No metrics exist, and
none may be quoted until the fields below are filled from an actual run.

| Field | Value |
| --- | --- |
| Task | Image classification (whole image; no localisation) |
| Classes | `background_folder_unconfirmed` (0), `visible_deterioration_folder` (1) — provisional names pending label review |
| Architecture | ResNet-18 (torchvision), ImageNet-1K initialisation |
| Preprocessing | `letterbox-rgb-imagenet-v1` (no cropping; see `vision/preprocessing/transforms.py`) |
| Training data | Darbhanga Fort folder dataset, single site — *pending audit* |
| Split | Group-aware (exact + near duplicates), stratified, seed 1337 — *pending* |
| Checkpoint | `vision/outputs/experiments/<name>/<run_id>/model.pt` (gitignored) — *none yet* |
| Validation metrics | *none* |
| Test metrics | *none* |
| Decision threshold | chosen on validation by max-F1 — *none* |
| Calibration | reported in `eval_val.json` — *none* |

## Intended use

Flag inspection photographs that look like the reviewed "visible deterioration" examples so a
person looks at them first. SEE stage only.

## Not supported

Locating defects; measuring crack width or area; estimating severity, risk, or urgency;
judging structural safety, material chemistry or groundwater; recommending repairs; any
structure type or site not represented in the evaluation data.

## Known limitations (already true before training)

* One site: results cannot show generalisation to other sites or water-structure types.
* Severe class imbalance (~17:1 in the earlier, unverified count).
* The negative folder includes visibly weathered surfaces, so the negative class is not
  "healthy".
* Related crops of the same wall may exist without metadata to group them; splits can only
  group exact and near duplicates.

## Reproduce

See `vision/README.md` → "Workflow".
