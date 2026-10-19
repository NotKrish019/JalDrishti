"""Detection metrics against hand-computed cases."""

from __future__ import annotations

import numpy as np
import pytest

from vision.metrics.detection import average_precision_101, box_iou, evaluate_detections, image_level_scores


def _im(gt, pred, scores):
    return {
        "gt": {"boxes": np.array(gt, dtype=float).reshape(-1, 4), "labels": np.zeros(len(gt), dtype=int)},
        "pred": {"boxes": np.array(pred, dtype=float).reshape(-1, 4), "labels": np.zeros(len(pred), dtype=int),
                 "scores": np.array(scores, dtype=float)},
    }


def test_box_iou_known_values() -> None:
    a = np.array([[0, 0, 10, 10]])
    b = np.array([[0, 0, 10, 10], [5, 0, 15, 10], [20, 20, 30, 30], [0, 0, 5, 5]])
    np.testing.assert_allclose(box_iou(a, b)[0], [1.0, 50 / 150, 0.0, 0.25])
    with pytest.raises(ValueError):
        box_iou(np.array([[10, 0, 0, 10]]), b)


def test_perfect_predictions_score_one() -> None:
    images = [_im([[0, 0, 10, 10]], [[0, 0, 10, 10]], [0.9]), _im([[5, 5, 50, 50]], [[5, 5, 50, 50]], [0.8])]
    r = evaluate_detections(images, ["crack"])
    assert r["map50"] == pytest.approx(1.0) and r["map50_95"] == pytest.approx(1.0)
    op = r["per_class"][0]["operating_point"]
    assert (op["true_positives"], op["false_positives"], op["missed"]) == (2, 0, 0)


def test_duplicate_detection_is_a_false_positive_and_misses_are_counted() -> None:
    images = [
        _im([[0, 0, 10, 10]], [[0, 0, 10, 10], [0, 0, 10, 10]], [0.9, 0.8]),  # second box is a duplicate
        _im([[0, 0, 10, 10]], [], []),  # missed
        _im([], [[0, 0, 10, 10]], [0.7]),  # false positive on a background image
    ]
    r = evaluate_detections(images, ["crack"])
    op = r["per_class"][0]["operating_point"]
    assert (op["true_positives"], op["false_positives"], op["missed"]) == (1, 2, 1)
    assert op["precision"] == pytest.approx(1 / 3) and op["recall"] == pytest.approx(0.5)
    # ranked: TP(0.9), FP(0.8), FP(0.7); recall reaches 0.5 at precision 1, never higher
    assert r["map50"] == pytest.approx(51 / 101)


def test_iou_threshold_controls_matching() -> None:
    images = [_im([[0, 0, 10, 10]], [[0, 0, 10, 7]], [0.9])]  # IoU 0.7
    r = evaluate_detections(images, ["crack"])
    assert r["per_class"][0]["ap50"] == pytest.approx(1.0)
    assert r["per_class"][0]["ap75"] == pytest.approx(0.0)
    assert 0 < r["map50_95"] < 1


def test_no_ground_truth_gives_undefined_ap() -> None:
    r = evaluate_detections([_im([], [[0, 0, 5, 5]], [0.6])], ["crack"])
    assert r["per_class"][0]["ap50"] is None and r["map50"] is None
    assert average_precision_101(np.zeros(0, bool), np.zeros(0), 0) is None
    assert average_precision_101(np.zeros(0, bool), np.zeros(0), 3) == 0.0


def test_malformed_inputs_rejected() -> None:
    bad = {"gt": {"boxes": np.zeros((1, 4))}, "pred": {"boxes": np.zeros((0, 4)), "labels": [], "scores": []}}
    with pytest.raises(ValueError):
        evaluate_detections([bad], ["crack"])
    mismatched = _im([[0, 0, 1, 1]], [[0, 0, 1, 1]], [0.5, 0.4])
    with pytest.raises(ValueError):
        evaluate_detections([mismatched], ["crack"])


def test_image_level_scores() -> None:
    images = [_im([[0, 0, 1, 1]], [[0, 0, 1, 1], [1, 1, 2, 2]], [0.3, 0.8]), _im([], [], [])]
    s = image_level_scores(images)
    assert s["y_true"].tolist() == [1, 0]
    assert s["score"].tolist() == [0.8, 0.0]
