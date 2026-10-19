# Experiment log

Every entry states exactly what ran. Pipeline tests on synthetic data are logged so the tooling
is traceable; their metrics say nothing about real-world performance and are not quoted.

## 2026-10-19 — pipeline verification (synthetic data only)

* **Machine:** Apple M2 (arm64), macOS; Python 3.14.3, torch 2.14.0, torchvision 0.29.0,
  numpy 2.4.3, Pillow 12.1.1. CUDA unavailable; Apple MPS available. Ultralytics and OpenCV
  not installed. This is **not** the GTX 1650 / CUDA 12.1 environment from the earlier report,
  which was not available for verification.
* **Data:** 121 generated images (60 per folder + 1 exact duplicate), created on the fly; no
  real dataset images used.
* **Commands:** `audit_dataset.py` → `make_contact_sheets.py` → `make_splits.py` →
  `train_classifier.py` (gate check, then `--allow-unverified-labels --no-pretrained --epochs 3
  --device cpu`) → `evaluate_classifier.py --split val`.
* **Outcome:** all steps completed. The gate rejected the unverified config (exit 2). The split
  kept 120 / excluded 1 (exact duplicate), 84 / 18 / 18 stratified, leakage check passed. The
  checkpoint is marked `label_status: unverified`. Validation outputs (report, TP/TN sheets)
  were written. **Status: pipeline verified; no model trained on real data.**

## 2026-10-19 — inference latency (random weights, runtime only)

`scripts/vision/benchmark_inference.py --random-init`, batch 1, 224×224 model input from a
768×768 JPEG decoded from memory (no disk I/O), 10 warm-up + 100 timed repetitions, device
synchronised before each timestamp. Median / p90 in milliseconds:

| Arch | Device | Load | Preprocess | Forward | Postprocess | Total |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| resnet18 | CPU | 152 | 6.96 / 7.30 | 12.05 / 13.37 | 0.01 / 0.02 | 19.06 / 20.44 |
| mobilenet_v3_small | CPU | 49 | 7.13 / 7.68 | 40.93 / 44.38 | 0.02 / 0.02 | 48.16 / 52.33 |
| resnet18 | MPS | 198 | 7.47 / 9.78 | 5.57 / 9.55 | 0.29 / 0.49 | 13.91 / 18.91 |
| mobilenet_v3_small | MPS | 109 | 7.32 / 8.30 | 6.79 / 9.33 | 0.30 / 0.34 | 14.40 / 16.99 |

These are architecture runtimes on this machine, not a trained model's performance, and they
do not predict GTX 1650 timings. Re-run on the deployment hardware.

## 2026-10-19 — audit of the supplied dataset

`DrabhangaDataset.zip` (outer zip → inner zip) extracted to `data/raw/darbhanga_crack/`.
4,259 images, all readable, 768 × 768 RGB; 3,843 YOLO label files, all valid; 1 class. The
published train/val/test split leaks (photometric copies of the same photographs across splits;
the test folder is unlabelled copies). Re-split by duplicate group. Full details in
`DATASET_AUDIT.md`.

## 2026-10-19 — `bounded_check` (detector, 20 batches)

`train_detector.py --epochs 1 --max-train-batches 20 --max-val-images 64`: loop, checkpointing
and evaluation verified; val mAP@0.5 0.0 (still in learning-rate warm-up), as expected.

## 2026-10-19 — `pilot_v1` (detector)

Faster R-CNN MobileNetV3-Large FPN from COCO weights, 512 px, batch 8, 8 epochs, CPU (Apple M2,
torch 2.14.0), 5,587 s. Best epoch 7 by val mAP@0.5 (0.826). Box threshold 0.70 (val max F1).
Test, evaluated once: mAP@0.5 0.855 (95% CI 0.800–0.906), mAP@0.5:0.95 0.605, precision 0.909,
recall 0.805 at 0.70 / IoU 0.5. Error analysis and caveats: `MODEL_CARD_crack_detector.md`.
**Status: training completed, with a documented baseline evaluation; appropriate for a limited
pilot on similar brick masonry only.**

## Next experiments

1. Second-annotator review of the val and test photographs; re-score against reviewed labels.
2. Collect crack-free photographs framed like the crack photographs (wider views, edges, windows)
   so false-alarm behaviour is measured on realistic negatives.
3. Add data from other sites and from stone masonry (baolis, kunds, tanks) and report per site.
4. Try 768 px input (no downscaling) for thin cracks; measure on the same split.
5. Measure latency on the deployment hardware.

## Superseded: classifier plan (folder dataset)

The steps below apply only if the folder-labelled dataset from the earlier report is supplied.


1. Run the audit on the real dataset; record counts, duplicates and cross-folder conflicts.
2. Review contact sheets; write `labels.semantics`; set `labels.verified: true`.
3. `make_splits.py`, then a bounded first run:
   `train_classifier.py --config vision/configs/classification_pilot.yaml --epochs 2 --max-train-batches 20`.
4. Full run (pretrained resnet18, 224 px, batch 16, class-weighted loss, early stopping on
   validation average precision). Evaluate on validation; inspect FP/FN sheets for shortcuts
   (sky, lighting, camera). Only then evaluate once on test and fill in the model card.
