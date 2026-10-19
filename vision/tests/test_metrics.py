"""Classification metrics against hand-computed toy cases."""

from __future__ import annotations

import numpy as np
import pytest

from vision.metrics.classification import (
    average_precision,
    calibration_report,
    classification_report,
    confusion_matrix,
    per_class_metrics,
    roc_auc,
    select_threshold,
)


def test_confusion_matrix_and_per_class() -> None:
    y_true = [0, 0, 0, 1, 1, 1, 1, 1]
    y_pred = [0, 1, 0, 1, 1, 0, 1, 1]
    cm = confusion_matrix(y_true, y_pred, 2)
    assert cm.tolist() == [[2, 1], [1, 4]]
    per = per_class_metrics(cm, ["a", "b"])
    assert per[0]["support"] == 3 and per[1]["support"] == 5
    assert per[1]["precision"] == pytest.approx(4 / 5)
    assert per[1]["recall"] == pytest.approx(4 / 5)
    assert per[0]["precision"] == pytest.approx(2 / 3)
    assert per[0]["f1"] == pytest.approx(2 / 3)


def test_absent_class_is_undefined_not_zero() -> None:
    cm = confusion_matrix([1, 1, 1], [1, 1, 1], 3)
    per = per_class_metrics(cm, ["a", "b", "c"])
    assert per[0]["recall"] is None and per[0]["precision"] is None and per[0]["support"] == 0
    assert per[0]["f1"] is None  # absent and never predicted: genuinely undefined
    assert per[1]["recall"] == 1.0


def test_never_predicted_class_counts_as_zero_f1_in_macro() -> None:
    # Model predicts the positive class for everything: macro F1 must reflect the ignored class.
    probs = np.array([[0.2, 0.8]] * 4)
    report = classification_report([0, 0, 1, 1], probs, ["neg", "pos"])
    assert report["per_class"][0]["f1"] == 0.0 and report["per_class"][0]["precision"] is None
    assert report["macro_f1"] == pytest.approx((0.0 + 2 / 3) / 2)
    assert report["balanced_accuracy"] == pytest.approx(0.5)


def test_invalid_labels_rejected() -> None:
    with pytest.raises(ValueError):
        confusion_matrix([0, 2], [0, 1], 2)
    with pytest.raises(ValueError):
        confusion_matrix([0, 1], [0], 2)
    with pytest.raises(ValueError):
        confusion_matrix([0.5, 1.0], [0, 1], 2)


def test_average_precision_known_values() -> None:
    assert average_precision([1, 1, 0, 0], [0.9, 0.8, 0.2, 0.1]) == pytest.approx(1.0)
    # ranking: 1, 0, 1 -> precision at the positives is 1 and 2/3; AP = (1 + 2/3) / 2
    assert average_precision([1, 0, 1], [0.9, 0.8, 0.7]) == pytest.approx((1 + 2 / 3) / 2)
    assert average_precision([0, 0], [0.4, 0.3]) is None


def test_average_precision_handles_ties() -> None:
    # all scores tied: a single operating point with precision = prevalence
    assert average_precision([1, 0, 0, 1], [0.5, 0.5, 0.5, 0.5]) == pytest.approx(0.5)


def test_roc_auc_known_values() -> None:
    assert roc_auc([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8]) == pytest.approx(0.75)
    assert roc_auc([0, 1], [0.5, 0.5]) == pytest.approx(0.5)
    assert roc_auc([1, 1], [0.2, 0.3]) is None


def test_threshold_selection() -> None:
    y = [0, 0, 1, 1, 1]
    s = [0.1, 0.6, 0.55, 0.8, 0.9]
    best = select_threshold(y, s, "f1")
    assert best["threshold"] == pytest.approx(0.55)
    assert best["recall"] == 1.0
    at = select_threshold(y, s, "recall_at", target=0.66)
    assert at["threshold"] == pytest.approx(0.8) and at["recall"] >= 0.66
    with pytest.raises(ValueError):
        select_threshold([0, 0], [0.1, 0.2])
    with pytest.raises(ValueError):
        select_threshold(y, s, "recall_at")


def test_calibration() -> None:
    perfect = calibration_report([0, 0, 1, 1], [0.0, 0.0, 1.0, 1.0], bins=2)
    assert perfect["expected_calibration_error"] == pytest.approx(0.0)
    off = calibration_report([0, 0], [0.9, 0.9], bins=10)
    assert off["expected_calibration_error"] == pytest.approx(0.9)


def test_classification_report_threshold_and_argmax() -> None:
    probs = np.array([[0.9, 0.1], [0.6, 0.4], [0.3, 0.7], [0.45, 0.55]])
    y = [0, 1, 1, 0]
    argmax = classification_report(y, probs, ["neg", "pos"])
    assert argmax["decision"] == {"rule": "argmax"}
    assert argmax["confusion_matrix"] == [[1, 1], [1, 1]]
    th = classification_report(y, probs, ["neg", "pos"], threshold=0.35)
    assert th["confusion_matrix"] == [[1, 1], [0, 2]]
    assert th["per_class"][1]["recall"] == 1.0
    assert th["average_precision"] is not None and th["roc_auc"] is not None
    assert "expected_calibration_error" in th["calibration"]
    with pytest.raises(ValueError):
        classification_report(y, probs[:, :1], ["neg", "pos"])
