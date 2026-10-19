# Vision inference interface — backend handoff (for Swastik)

Two predictors share the same input handling, error codes and conventions:

* **`DetectionPredictor` — use this.** Crack detection pilot `pilot_v1` (trained, evaluated;
  see `MODEL_CARD_crack_detector.md`). Schema: `vision/configs/inference_output_detection.schema.json`.
* `ImageClassifierPredictor` — for a future folder-labelled classifier; no trained model yet.
  Schema: `vision/configs/inference_output.schema.json`.

## Crack detector

```python
from vision.inference import DetectionPredictor, DetectorLoadError, validate_detection_result

detector = DetectionPredictor.from_checkpoint(
    "vision/models/crack_detector_pilot_v1/model.pt", device="cpu")  # once
result = detector.predict(image_bytes)
payload = result.to_dict()
validate_detection_result(payload)   # optional
```

The checkpoint (76 MB) is tracked at `vision/models/crack_detector_pilot_v1/model.pt` with its
SHA-256 in `model.pt.sha256` and the run's metadata and evaluation reports alongside. It needs torch + torchvision; ~650 ms to load and
~100 ms per 768 × 768 image on an Apple M2 CPU.

Real output on a validation image:

```json
{
  "status": "ok",
  "task_type": "object_detection",
  "schema_version": "1.0",
  "model_name": "jaldrishti-darbhanga_crack_detection_pilot",
  "model_version": "pilot_v1",
  "label_status": "verified",
  "preprocessing_version": "rgb-01-torchvision-rcnn-resize-v1",
  "image": {"width": 768, "height": 768},
  "score_threshold": 0.7,
  "detections": [
    {"class_id": 0, "class_name": "crack", "confidence": 0.951, "bbox": [142.7, 51.7, 275.5, 425.4]}
  ],
  "image_level": {"max_score": 0.951, "threshold": 0.7, "candidate_present": true},
  "warnings": [],
  "error": null,
  "timing_ms": {"preprocess": 8.4, "forward": 96.2, "postprocess": 0.0, "total": 104.7},
  "disclaimer": "Candidate crack regions for human review. ..."
}
```

* `bbox` is `[x_min, y_min, x_max, y_max]` in pixels of the decoded input (after EXIF rotation).
* Only boxes with `confidence >= score_threshold` are returned. `image_level.candidate_present`
  is true exactly when at least one box is returned.
* A warning is added when the input is not 768 × 768 (the training size).
* Mapping to `contracts/vision_result.schema.json`: each detection can fill `class_name`,
  `confidence` and `bounding_box`. The contract also requires `pixel_area`, `coverage_ratio` and
  `component_count`; for a box detector the honest values are the **box** area, box-area ratio
  and 1, and they should be documented as box-based, not crack-pixel measurements. Do not fill
  `total_length_pixels`, `relative_severity` or any width field from this model.

## Image classifier (no trained model yet)

## Ownership

* Vision (Krish): `ImageClassifierPredictor` — validate image, preprocess, run model,
  postprocess, return a structured result.
* Backend (Swastik): receive uploads, Cloudinary storage, associating results with an
  inspection, the HTTP API. The vision package contains no Cloudinary code or credentials.

## Usage

```python
from vision.inference import ImageClassifierPredictor, ModelLoadError, validate_result

predictor = ImageClassifierPredictor.from_checkpoint("path/to/model.pt", device="auto")  # once, at startup
result = predictor.predict(image_bytes)   # bytes, path, PIL.Image, or HxWx3 uint8 RGB array
payload = result.to_dict()                # JSON-serialisable
validate_result(payload)                  # optional: checks vision/configs/inference_output.schema.json
```

* `from_checkpoint` raises `ModelLoadError` for a missing, unreadable, mislabelled or
  incompatible checkpoint (wrong format, invalid class mapping, preprocessing mismatch).
  Checkpoints are loaded with `torch.load(weights_only=True)`.
* `predict` never raises for bad input. It returns `status: "error"` with a stable code:
  `not_found`, `empty_input`, `too_large`, `too_small`, `unsupported_format`,
  `unsupported_input`, `unsupported_array`, `unreadable_image`, `inference_failed`.
* Limits (`ImageLimits`): 32 px minimum side, 12,000 px maximum side, 60 MP, 30 MB,
  JPEG/PNG/WEBP/BMP/TIFF. EXIF orientation is applied; the input is never mutated.
* One forward pass runs at a time per predictor (a lock), so memory stays bounded under
  concurrent requests. Reuse one predictor; do not load per request.
* Device: `auto` picks CUDA, then Apple MPS, then CPU.

## Output (real example from a smoke-test checkpoint on synthetic data)

```json
{
  "status": "ok",
  "task_type": "image_classification",
  "schema_version": "1.0",
  "model_name": "jaldrishti-darbhanga_image_level_pilot",
  "model_version": "smoke",
  "label_status": "unverified",
  "preprocessing_version": "letterbox-rgb-imagenet-v1",
  "image": {"width": 128, "height": 128},
  "predictions": [
    {"class_id": 0, "class_name": "background_folder_unconfirmed", "score": 0.7855},
    {"class_id": 1, "class_name": "visible_deterioration_folder", "score": 0.2145}
  ],
  "top_class": "background_folder_unconfirmed",
  "decision": {"rule": "score_threshold", "positive_class": "visible_deterioration_folder",
               "threshold": 0.193, "positive": true},
  "warnings": ["This model was trained on unverified folder labels and is a pipeline test only. Its outputs must not be shown as findings."],
  "error": null,
  "timing_ms": {"preprocess": 6.06, "forward": 5.48, "postprocess": 0.02, "total": 11.56},
  "disclaimer": "Image-level model output for human review. ..."
}
```

Error example: `{"status": "error", "predictions": [], "error": {"code": "unreadable_image", "message": "Image could not be decoded: UnidentifiedImageError"}, ...}`.

### How to read it

* **Use `decision.positive` when `decision` is present, not `top_class`.** `top_class` is the
  arg-max class. `decision` applies the threshold chosen on the validation split (often well
  below 0.5 for an imbalanced positive class). In the example they disagree, and the decision
  is the one the model was tuned for.
* `score` is a softmax output, not a calibrated probability that damage exists. The
  evaluation report includes a calibration table; treat scores as ranking signals unless the
  model card says the model was calibrated.
* There are **no** bounding boxes, masks, severity, or safety fields: this model classifies the
  whole image. A "positive" result means "this image resembles the training examples of the
  deterioration class — review it", nothing more.
* Show `warnings` and `disclaimer` to users. If `label_status` is `unverified`, do not show the
  result as a finding at all.

## Mapping to `contracts/vision_result.schema.json`

The shared contract expects detections with `bounding_box`, `pixel_area` and
`coverage_ratio`. An image-level classifier cannot fill those honestly. Options for the team:

1. Add an optional `image_level_observations` array to the shared contract
   (`[{class_name, score, decision}]`) and leave `detections` empty for classifier results; or
2. Keep classifier output in a separate field of the inspection record.

Either needs agreement between Swastik (contract owner) and Krish. Do not translate a
classifier score into a full-image bounding box.
