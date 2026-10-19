# Dataset audit

Owner: Krish (Computer Vision / AI) · Audited 2026-10-19 on the archive supplied in the repo root

## Source

* Supplied file: `DrabhangaDataset.zip` (362 MB, repository root, untracked). It contains one
  inner archive, `Brick Masonry Crack Dataset Collected from Battledore of Darbhanga Fort
  (A Cultural Heritage) for Automatic Crack Detection/Crack Data-Darbhanga Fort.zip`.
* Extracted with path-traversal checks to `data/raw/darbhanga_crack/` (gitignored by
  `data/raw/*`). Neither the images nor the archive should be committed.
* **Provenance and licence: not recorded in the archive.** No README, citation, DOI or licence
  file is included. The title matches a published dataset; Krish should record its citation and
  licence here before any redistribution, including the seven images in `vision/demo_assets/`.

### Discrepancy with the earlier report

The earlier report described `Darbhanga_Fort/Darbhanga_Fort/{Damaged_images, Background_images}`
with 7,440 + 446 = 7,886 images and **no annotations**. The supplied archive is a different
packaging: 4,259 images in `train/ val/ test/` with **YOLO bounding-box labels**. The figures
below replace the earlier ones; the earlier dataset was not available to audit.

## Images (all 4,259 decoded)

| Folder | Images | Label files |
| --- | ---: | ---: |
| `train/images` | 3,407 | 3,204 (+ `classes.txt`) |
| `val/images` | 639 | 639 (+ `classes.txt`) |
| `test` | 213 | 0 |

* Format: JPEG, RGB, 768 × 768 for every image. No unreadable, empty or truncated files; no
  quality flags.

## Labels (all 3,843 label files validated)

* One class: `crack`. Format: YOLO `class xc yc w h`, normalised.
* No malformed lines, no out-of-range coordinates, no boxes extending beyond the image, no
  zero-area boxes, no label files without an image.
* Train: 4,583 boxes on 3,204 images (1 box: 2,251 images; 2: 631; 3: 239; 4+: 83).
  Val: 922 boxes on 639 images.
* Box area as a fraction of the image (train): median 0.065, 10th percentile 0.007, 90th
  percentile 0.36; 254 boxes cover more than half the image.
* **203 train images have no label file** (`train (3205)`–`train (3407)`). A visual sample shows
  close-up brick with weathering and blackening but no visible crack: treated as background
  (negative) images. The `test/` folder has no labels at all.
* **Visual spot check** (`vision/outputs/audit/labelled_boxes_review.jpg`, 18 random images):
  most boxes enclose visible cracks; several are loose or questionable, e.g. a box along an
  entire mortar course, a box on a window jamb edge. Labels are useful but noisy.

What a box asserts: an annotator marked a region of brick masonry containing a visible crack.
It does not encode crack width, depth, cause, activity or structural significance.

## Duplicates and leakage

Method: SHA-256 for exact copies; 64-bit dHash, Hamming distance ≤ 6, for near copies (banded
search, exhaustive up to 7).

* 167 exact-duplicate groups (167 redundant files).
* 4,294 near-duplicate pairs (distance 0: 611, 1: 1,131, 2: 1,096, 3: 705, 4: 458, 5: 203, 6: 90).
* Connected groups: 1,304, up to 6 images each, covering 4,054 of 4,259 images.
* Visual check (`vision/outputs/audit/duplicate_groups_review.jpg`): group members are the same
  photograph with different brightness, contrast or saturation. **The dataset is roughly 1,500
  distinct photographs, each present in several photometric variants.**
* Within duplicate groups that have more than one label file, 1,070 carry identical boxes and
  223 carry different boxes. The variants were labelled separately, which adds annotation noise.
* **The published split leaks.** 36 val images and 3 test images are byte-identical to train
  images; 1,511 near-duplicate pairs cross the published splits; 211 of the 213 `test/` images
  are copies of labelled train/val images. Scores on the published val split would be inflated.
* No group mixes crack-labelled and background images.

## Split used (`scripts/vision/make_detection_splits.py`, seed 1337)

The published folders are ignored. All labelled images are regrouped by duplicate group and
assigned whole to a split, stratified by crack/background:

| Split | Images | Distinct photographs | Crack | Background |
| --- | ---: | ---: | ---: | ---: |
| train | 2,822 | 1,055 | 2,680 | 142 |
| val | 226 | 226 | 197 | 29 |
| test | 226 | 226 | 197 | 29 |

* Train keeps every photometric copy (each was labelled); val and test keep one representative
  per photograph. Excluded: 772 duplicate copies (val/test only), 213 unlabelled `test/` images.
* Leakage check passed: no duplicate group and no identical content appears in two splits.

## Remaining limitations

* **One site.** Every image is from Darbhanga Fort brick masonry. No split of this data can
  measure performance on other sites, stone masonry, or other water structures (baolis, kunds,
  tanks).
* Related-but-different photographs of the same wall (not photometric copies) cannot be found
  by hashing; some may still straddle splits.
* Background images are visually distinct close-ups, so the image-level crack/background
  distinction may partly reflect framing rather than cracks.
* Licence and citation unknown.

## Reproduce

```bash
python3 scripts/vision/audit_dataset.py --data-dir "data/raw/darbhanga_crack/Crack Data-Darbhanga Fort" --out vision/outputs/audit
python3 scripts/vision/make_detection_splits.py --config vision/configs/detection_pilot.yaml --manifest vision/outputs/audit/manifest.jsonl
```
