# Model card — crack detection pilot `pilot_v1`

Status: **trained and evaluated as a limited pilot.** Suitable for proposing candidate crack
regions in photographs of brick masonry similar to the training data, for human review. Not
validated for any other site, material or structure type, and not production-ready.

| Field | Value |
| --- | --- |
| Task | Object detection, 1 class: `crack` |
| Architecture | torchvision Faster R-CNN, MobileNetV3-Large FPN backbone |
| Initial weights | torchvision `FasterRCNN_MobileNet_V3_Large_FPN_Weights.COCO_V1` (sha256 prefix `fb6a3cc7`) |
| Data | Darbhanga Fort brick-masonry crack dataset (`DrabhangaDataset.zip`), YOLO boxes; licence not recorded |
| Split | Leakage-safe re-split by duplicate group, seed 1337: train 2,822 images (1,055 photographs), val 226, test 226 |
| Input | RGB, resized inside the model to 512 px (training images 768 × 768) |
| Training | 8 epochs, SGD lr 0.01 (200-step warm-up, cosine), batch 8, h-flip + colour jitter; CPU, Apple M2, 93 min |
| Selection | Best epoch by validation mAP@0.5 → epoch 7 |
| Box threshold | 0.70, chosen on validation (max box F1 @ IoU 0.5) |
| Image flag | Candidate present ⇔ at least one box ≥ 0.70 |
| Checkpoint | `vision/models/crack_detector_pilot_v1/model.pt` (76 MB, tracked; SHA-256 in `model.pt.sha256`; run metadata alongside) |

## Results

Test split, evaluated once after the model and threshold were fixed (226 photographs: 197 with
annotated cracks, 29 background; 261 annotated boxes). 95% intervals are from 500 bootstrap
resamples over images.

| Metric | Validation | Test |
| --- | ---: | ---: |
| mAP@0.5 | 0.826 | **0.855** (0.800–0.906) |
| mAP@0.5:0.95 | 0.613 | 0.605 |
| AP@0.75 | 0.651 | 0.637 |
| Box precision @ 0.70, IoU 0.5 | 0.896 (215 TP / 25 FP) | **0.909** (0.868–0.943) |
| Box recall @ 0.70, IoU 0.5 | 0.785 (59 missed) | **0.805** (0.753–0.857) |
| Image flag: crack images flagged | 189 / 197 | 193 / 197 |
| Image flag: backgrounds not flagged | 28 / 29 | 29 / 29 |

Training curve (validation mAP@0.5 by epoch): 0.685, 0.777, 0.802, 0.791, 0.818, 0.809, **0.826**, 0.823.

## How to read these numbers

* **Box metrics are measured against noisy labels.** Error review on validation
  (`eval_val_misses.jpg`, `eval_val_false_alarms.jpg`) shows many "false positives" are visible
  cracks the annotator boxed differently or not at all, and many "misses" are tiny or faint
  boxes, or one large labelled box where the model drew several smaller ones (or vice versa).
  Photometric copies of the same photograph carry different boxes in 223 groups.
* **The image-level result is probably optimistic.** The 29 test backgrounds come from one
  visually distinct batch of close-up brick textures; on 28 of them the model proposes no
  region at all. Separating that batch is easy and may rely on framing rather than cracks.
  There is no evidence yet about crack-free photographs taken the way crack photographs were.
* **One site, one material.** All data is brick masonry from Darbhanga Fort. On four stone
  stepwell photographs (out of domain) the model returned no boxes, which is the safe outcome,
  but that is a sanity check, not an evaluation.
* Scores are detector confidences, not calibrated probabilities.

## A decision changed after looking at out-of-domain images

Training also selected an image-level threshold of 0.052 (max F1 on validation). It flagged 3
of 4 stone stepwell photographs as "candidate present" while returning no box on any of them.
The image flag was therefore redefined as "at least one box ≥ the box threshold", so the flag
and the boxes always agree. This change was made on design grounds; both rules are reported in
`image_level_rule_comparison.json` (old rule on test: 197/197 crack images flagged, 1 of 29
backgrounds wrongly flagged).

## Intended use

SEE stage: surface photographs and regions that may show cracks so a person reviews them first,
and keep that evidence attached to an inspection.

## Not supported

Crack width, length, depth, orientation or activity; cause; severity, risk or urgency;
structural safety; material identification; repair recommendations; stone masonry, plaster,
other sites, or other water-structure types; anything other than cracks (vegetation, material
loss, staining and joints are not labelled).

## Runtime

CPU, Apple M2, torch 2.14.0, 4 threads, one 768 × 768 JPEG decoded from memory, 5 warm-up +
50 timed runs: model load 650 ms; per image median 97 ms (p90 103 ms), of which the forward
pass is 95 ms. GTX 1650 / CUDA timings have not been measured.

## Reproduce

See `vision/README.md` → "Workflow — crack detection". Artefacts in the run directory:
`run.json` (config, versions, manifest hash), `history.json`, `val_report.json`, `eval_val.json`,
`eval_test.json`, `test_bootstrap.json`, `image_level_rule_comparison.json`, review sheets.
