"""Image-classification metrics, implemented directly so they are easy to audit and test.

Conventions:
* y_true / y_pred are integer class ids in [0, n_classes).
* For binary ranking metrics, `scores` is the model score for the positive class.
* Where a quantity is undefined (e.g. precision with no predicted positives), it is reported
  as None rather than silently as 0, and the report lists the undefined fields.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

import numpy as np


def _as_labels(y: Sequence[int], n_classes: int, name: str) -> np.ndarray:
    arr = np.asarray(y)
    if arr.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")
    if arr.size and (not np.issubdtype(arr.dtype, np.integer)):
        raise ValueError(f"{name} must contain integer class ids")
    if arr.size and (arr.min() < 0 or arr.max() >= n_classes):
        raise ValueError(f"{name} contains ids outside [0, {n_classes})")
    return arr.astype(np.int64)


def confusion_matrix(y_true: Sequence[int], y_pred: Sequence[int], n_classes: int) -> np.ndarray:
    """Rows are true classes, columns predicted classes."""
    t = _as_labels(y_true, n_classes, "y_true")
    p = _as_labels(y_pred, n_classes, "y_pred")
    if t.shape != p.shape:
        raise ValueError("y_true and y_pred must have the same length")
    cm = np.zeros((n_classes, n_classes), dtype=np.int64)
    np.add.at(cm, (t, p), 1)
    return cm


def per_class_metrics(cm: np.ndarray, class_names: Sequence[str]) -> List[Dict]:
    out = []
    for i, name in enumerate(class_names):
        tp = int(cm[i, i])
        support = int(cm[i].sum())
        predicted = int(cm[:, i].sum())
        precision = tp / predicted if predicted else None
        recall = tp / support if support else None
        # F1 = 2TP / (2TP + FP + FN). A class with examples that is never predicted scores 0,
        # not "undefined": otherwise macro averages hide a model that ignores a class.
        # It is undefined only when the class is neither present nor predicted.
        f1 = (2 * tp / (support + predicted)) if (support + predicted) else None
        out.append(
            {"class_id": i, "class_name": name, "precision": precision, "recall": recall, "f1": f1,
             "support": support, "predicted": predicted}
        )
    return out


def average_precision(y_true: Sequence[int], scores: Sequence[float]) -> Optional[float]:
    """Area under the precision-recall curve (step-wise, as average precision).
    Returns None when there are no positives."""
    t = np.asarray(y_true).astype(np.int64)
    s = np.asarray(scores, dtype=np.float64)
    if t.shape != s.shape:
        raise ValueError("y_true and scores must have the same length")
    n_pos = int(t.sum())
    if n_pos == 0:
        return None
    order = np.argsort(-s, kind="mergesort")
    t, s = t[order], s[order]
    # Evaluate at distinct score thresholds so tied scores are treated together.
    distinct = np.r_[np.where(np.diff(s))[0], t.size - 1]
    tps = np.cumsum(t)[distinct]
    fps = (distinct + 1) - tps
    precision = tps / (tps + fps)
    recall = tps / n_pos
    recall_prev = np.r_[0.0, recall[:-1]]
    return float(np.sum((recall - recall_prev) * precision))


def roc_auc(y_true: Sequence[int], scores: Sequence[float]) -> Optional[float]:
    """Mann-Whitney formulation with average ranks for ties. None if one class is absent."""
    t = np.asarray(y_true).astype(np.int64)
    s = np.asarray(scores, dtype=np.float64)
    n_pos, n_neg = int(t.sum()), int((1 - t).sum())
    if n_pos == 0 or n_neg == 0:
        return None
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s), dtype=np.float64)
    sorted_s = s[order]
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and sorted_s[j + 1] == sorted_s[i]:
            j += 1
        ranks[order[i : j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return float((ranks[t == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def select_threshold(
    y_true: Sequence[int], scores: Sequence[float], criterion: str = "f1", target: Optional[float] = None
) -> Dict:
    """Choose a decision threshold for the positive class. Use on VALIDATION data only.

    criterion:
        "f1"            maximise F1 of the positive class
        "recall_at"     highest threshold whose recall >= target (prefer precision at that recall)
    """
    t = np.asarray(y_true).astype(np.int64)
    s = np.asarray(scores, dtype=np.float64)
    if t.size == 0 or t.sum() == 0:
        raise ValueError("threshold selection needs at least one positive example")
    candidates = np.unique(s)
    best = None
    for th in candidates:
        pred = (s >= th).astype(np.int64)
        tp = int(((pred == 1) & (t == 1)).sum())
        fp = int(((pred == 1) & (t == 0)).sum())
        fn = int(((pred == 0) & (t == 1)).sum())
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn)
        f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
        row = {"threshold": float(th), "precision": precision, "recall": recall, "f1": f1}
        if criterion == "f1":
            if best is None or f1 > best["f1"] or (f1 == best["f1"] and th > best["threshold"]):
                best = row
        elif criterion == "recall_at":
            if target is None:
                raise ValueError("recall_at requires a target recall")
            if recall >= target and (best is None or th > best["threshold"]):
                best = row
        else:
            raise ValueError(f"unknown criterion {criterion!r}")
    if best is None:
        raise ValueError("no threshold satisfies the criterion")
    return {"criterion": criterion, "target": target, **best}


def calibration_report(y_true: Sequence[int], scores: Sequence[float], bins: int = 10) -> Dict:
    """Expected calibration error and a reliability table for positive-class scores."""
    t = np.asarray(y_true).astype(np.float64)
    s = np.asarray(scores, dtype=np.float64)
    if t.size == 0:
        raise ValueError("calibration needs at least one sample")
    edges = np.linspace(0.0, 1.0, bins + 1)
    idx = np.clip(np.digitize(s, edges[1:-1], right=True), 0, bins - 1)
    table, ece = [], 0.0
    for b in range(bins):
        m = idx == b
        n = int(m.sum())
        if n == 0:
            table.append({"bin": [float(edges[b]), float(edges[b + 1])], "count": 0, "mean_score": None, "positive_rate": None})
            continue
        conf, acc = float(s[m].mean()), float(t[m].mean())
        ece += n / t.size * abs(conf - acc)
        table.append({"bin": [float(edges[b]), float(edges[b + 1])], "count": n, "mean_score": conf, "positive_rate": acc})
    return {"expected_calibration_error": ece, "bins": table}


def classification_report(
    y_true: Sequence[int],
    probabilities: np.ndarray,
    class_names: Sequence[str],
    threshold: Optional[float] = None,
    positive_class: int = 1,
) -> Dict:
    """Full report from per-class probabilities (N x C).

    Binary tasks use `threshold` on the positive-class score when given (it must have been
    selected on validation data); otherwise the arg-max class is predicted.
    """
    probs = np.asarray(probabilities, dtype=np.float64)
    n_classes = len(class_names)
    if probs.ndim != 2 or probs.shape[1] != n_classes:
        raise ValueError(f"probabilities must be N x {n_classes}")
    t = _as_labels(y_true, n_classes, "y_true")
    if probs.shape[0] != t.size:
        raise ValueError("probabilities and y_true must have the same length")

    if n_classes == 2 and threshold is not None:
        y_pred = (probs[:, positive_class] >= threshold).astype(np.int64)
        if positive_class == 0:
            y_pred = 1 - y_pred
        decision = {"rule": "threshold", "threshold": threshold, "positive_class": class_names[positive_class]}
    else:
        y_pred = probs.argmax(axis=1)
        decision = {"rule": "argmax"}

    cm = confusion_matrix(t, y_pred, n_classes)
    per_class = per_class_metrics(cm, class_names)
    recalls = [c["recall"] for c in per_class if c["recall"] is not None]
    f1s = [c["f1"] for c in per_class if c["f1"] is not None]
    report = {
        "n_samples": int(t.size),
        "class_names": list(class_names),
        "decision": decision,
        "confusion_matrix": cm.tolist(),
        "per_class": per_class,
        "accuracy": float((cm.trace() / t.size)) if t.size else None,
        "balanced_accuracy": float(np.mean(recalls)) if recalls else None,
        "macro_f1": float(np.mean(f1s)) if f1s else None,
        "undefined": [f"{c['class_name']}.{k}" for c in per_class for k in ("precision", "recall", "f1") if c[k] is None],
    }
    if n_classes == 2:
        pos = (t == positive_class).astype(np.int64)
        report["average_precision"] = average_precision(pos, probs[:, positive_class])
        report["roc_auc"] = roc_auc(pos, probs[:, positive_class])
        report["calibration"] = calibration_report(pos, probs[:, positive_class])
    return report
