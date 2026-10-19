"""Object-detection metrics (single or multiple classes), implemented to be auditable.

Boxes are [x1, y1, x2, y2] in pixels. Matching follows the COCO convention: per class and
image, predictions are taken in descending score order and each is matched to the unmatched
ground-truth box with the highest IoU at or above the threshold. AP is the area under the
101-point interpolated precision-recall curve.

Thin, diagonal cracks make box IoU a harsh measure: a box around half a crack and a box around
the whole crack can overlap little. Reports therefore include AP at IoU 0.5 and 0.5:0.95, an
operating-point summary at a fixed score threshold, and image-level metrics ("does this image
contain at least one crack box?"), which is how the product is likely to use the model.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

import numpy as np

COCO_IOUS = tuple(np.round(np.arange(0.5, 0.96, 0.05), 2))


def box_iou(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Pairwise IoU between N x 4 and M x 4 arrays of [x1, y1, x2, y2]."""
    a = np.asarray(a, dtype=np.float64).reshape(-1, 4)
    b = np.asarray(b, dtype=np.float64).reshape(-1, 4)
    if (a[:, 2:] < a[:, :2]).any() or (b[:, 2:] < b[:, :2]).any():
        raise ValueError("boxes must satisfy x2 >= x1 and y2 >= y1")
    ix1 = np.maximum(a[:, None, 0], b[None, :, 0])
    iy1 = np.maximum(a[:, None, 1], b[None, :, 1])
    ix2 = np.minimum(a[:, None, 2], b[None, :, 2])
    iy2 = np.minimum(a[:, None, 3], b[None, :, 3])
    inter = np.clip(ix2 - ix1, 0, None) * np.clip(iy2 - iy1, 0, None)
    area_a = (a[:, 2] - a[:, 0]) * (a[:, 3] - a[:, 1])
    area_b = (b[:, 2] - b[:, 0]) * (b[:, 3] - b[:, 1])
    union = area_a[:, None] + area_b[None, :] - inter
    return np.where(union > 0, inter / np.where(union > 0, union, 1), 0.0)


def _match(pred_boxes: np.ndarray, pred_scores: np.ndarray, gt_boxes: np.ndarray, iou_thr: float) -> np.ndarray:
    """Return a boolean array: is each prediction (in descending score order) a true positive."""
    order = np.argsort(-pred_scores, kind="mergesort")
    tp = np.zeros(len(order), dtype=bool)
    if len(gt_boxes) == 0 or len(order) == 0:
        return tp
    ious = box_iou(pred_boxes[order], gt_boxes)
    taken = np.zeros(len(gt_boxes), dtype=bool)
    for i in range(len(order)):
        cand = np.where(~taken, ious[i], -1.0)
        j = int(np.argmax(cand))
        if cand[j] >= iou_thr:
            taken[j] = True
            tp[i] = True
    return tp


def average_precision_101(tp: np.ndarray, scores: np.ndarray, n_gt: int) -> Optional[float]:
    """COCO 101-point interpolated AP from per-prediction TP flags pooled over images."""
    if n_gt == 0:
        return None
    if len(scores) == 0:
        return 0.0
    order = np.argsort(-scores, kind="mergesort")
    tp = tp[order].astype(np.float64)
    ctp, cfp = np.cumsum(tp), np.cumsum(1.0 - tp)
    recall = ctp / n_gt
    precision = ctp / np.maximum(ctp + cfp, np.finfo(np.float64).eps)
    # precision envelope (monotonically non-increasing from the right)
    for i in range(len(precision) - 2, -1, -1):
        precision[i] = max(precision[i], precision[i + 1])
    points = np.linspace(0, 1, 101)
    idx = np.searchsorted(recall, points, side="left")
    sampled = np.array([precision[i] if i < len(precision) else 0.0 for i in idx])
    return float(sampled.mean())


def _validate(images: Sequence[Dict], key: str) -> None:
    for i, im in enumerate(images):
        for field in ("boxes", "labels"):
            if field not in im[key]:
                raise ValueError(f"image {i}: {key} missing {field!r}")
        n = len(im[key]["boxes"])
        if len(im[key]["labels"]) != n or (key == "pred" and len(im[key].get("scores", [])) != n):
            raise ValueError(f"image {i}: {key} boxes/labels/scores lengths differ")


def evaluate_detections(
    images: Sequence[Dict],
    class_names: Sequence[str],
    iou_thresholds: Sequence[float] = COCO_IOUS,
    score_threshold: float = 0.5,
    operating_iou: float = 0.5,
) -> Dict:
    """Evaluate a dataset of predictions against ground truth.

    images: [{"gt": {"boxes": Nx4, "labels": N}, "pred": {"boxes": Mx4, "labels": M, "scores": M}}, ...]
    Label ids are 0-based indices into class_names.
    """
    _validate(images, "gt")
    _validate(images, "pred")
    per_class: List[Dict] = []
    for c, name in enumerate(class_names):
        n_gt = 0
        aps = {}
        for thr in iou_thresholds:
            tps, scs = [], []
            n_gt = 0
            for im in images:
                g = np.asarray(im["gt"]["boxes"], dtype=np.float64).reshape(-1, 4)[np.asarray(im["gt"]["labels"]) == c]
                pm = np.asarray(im["pred"]["labels"]) == c
                pb = np.asarray(im["pred"]["boxes"], dtype=np.float64).reshape(-1, 4)[pm]
                ps = np.asarray(im["pred"]["scores"], dtype=np.float64)[pm]
                n_gt += len(g)
                tps.append(_match(pb, ps, g, thr))
                scs.append(ps[np.argsort(-ps, kind="mergesort")])  # same order as the TP flags
            aps[float(thr)] = average_precision_101(np.concatenate(tps) if tps else np.zeros(0, bool),
                                                    np.concatenate(scs) if scs else np.zeros(0), n_gt)

        # Operating point at a fixed score threshold.
        tp_n = fp_n = 0
        for im in images:
            g = np.asarray(im["gt"]["boxes"], dtype=np.float64).reshape(-1, 4)[np.asarray(im["gt"]["labels"]) == c]
            keep = (np.asarray(im["pred"]["labels"]) == c) & (np.asarray(im["pred"]["scores"]) >= score_threshold)
            pb = np.asarray(im["pred"]["boxes"], dtype=np.float64).reshape(-1, 4)[keep]
            ps = np.asarray(im["pred"]["scores"], dtype=np.float64)[keep]
            tp = _match(pb, ps, g, operating_iou)
            tp_n += int(tp.sum())
            fp_n += int((~tp).sum())
        valid = [v for v in aps.values() if v is not None]
        per_class.append({
            "class_id": c,
            "class_name": name,
            "n_ground_truth": n_gt,
            "ap50": aps.get(0.5),
            "ap75": aps.get(0.75),
            "ap50_95": float(np.mean(valid)) if valid and len(valid) == len(iou_thresholds) else None,
            "operating_point": {
                "score_threshold": score_threshold,
                "iou": operating_iou,
                "true_positives": tp_n,
                "false_positives": fp_n,
                "missed": n_gt - tp_n,
                "precision": tp_n / (tp_n + fp_n) if tp_n + fp_n else None,
                "recall": tp_n / n_gt if n_gt else None,
            },
        })

    def mean(key: str) -> Optional[float]:
        vals = [p[key] for p in per_class if p[key] is not None]
        return float(np.mean(vals)) if vals else None

    return {
        "n_images": len(images),
        "class_names": list(class_names),
        "map50": mean("ap50"),
        "map50_95": mean("ap50_95"),
        "per_class": per_class,
        "ap_method": "COCO 101-point interpolation, greedy matching by score",
    }


def image_level_scores(images: Sequence[Dict]) -> Dict[str, np.ndarray]:
    """Image-level view: label = any ground-truth box; score = highest predicted box score (0 if none)."""
    y = np.array([1 if len(im["gt"]["boxes"]) else 0 for im in images], dtype=np.int64)
    s = np.array([float(np.max(im["pred"]["scores"])) if len(im["pred"]["scores"]) else 0.0 for im in images])
    return {"y_true": y, "score": s}
