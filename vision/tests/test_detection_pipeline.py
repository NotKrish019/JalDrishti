"""YOLO label validation, detection splits, a bounded CPU training run and the detection contract.

All data is synthetic and the detector starts from random weights (no download), so the run only
proves the pipeline; its metrics are meaningless.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw

torch = pytest.importorskip("torch")
pytest.importorskip("torchvision")

from vision.data.duplicates import find_duplicates  # noqa: E402
from vision.data.manifest import build_manifest, write_manifest  # noqa: E402
from vision.data.splits import check_leakage, make_group_splits  # noqa: E402
from vision.data.yolo_labels import check_split, parse_label_file, summarise  # noqa: E402
from vision.inference.detector import (  # noqa: E402
    DETECTOR_FORMAT,
    DetectionPredictor,
    DetectorLoadError,
    validate_detection_result,
)
from vision.training.config import ConfigError  # noqa: E402
from vision.training.detection import (  # noqa: E402
    DetectionConfig,
    label_path_for,
    load_targets,
    train_detector,
)


def _yolo_dataset(root: Path) -> Path:
    rng = np.random.default_rng(0)
    for split, n in (("train", 18), ("val", 6)):
        (root / split / "images").mkdir(parents=True)
        (root / split / "labels").mkdir()
        (root / split / "labels" / "classes.txt").write_text("crack\n")
        for i in range(n):
            img = Image.fromarray(rng.integers(100, 160, (16, 16, 3), dtype=np.uint8)).resize((128, 128))
            x0, y0 = int(rng.integers(10, 60)), int(rng.integers(10, 60))
            ImageDraw.Draw(img).line([(x0, y0), (x0 + 40, y0 + 50)], fill=(10, 10, 10), width=4)
            img.save(root / split / "images" / f"{split} ({i}).jpg", quality=92)
            xc, yc = (x0 + 20) / 128, (y0 + 25) / 128
            (root / split / "labels" / f"{split} ({i}).txt").write_text(f"0 {xc:.4f} {yc:.4f} {44 / 128:.4f} {54 / 128:.4f}\n")
        if split == "train":  # two background images without label files
            for j in range(2):
                Image.fromarray(rng.integers(100, 160, (16, 16, 3), dtype=np.uint8)).resize((128, 128)).save(
                    root / split / "images" / f"bg ({j}).jpg")
    (root / "test").mkdir()
    Image.new("RGB", (128, 128), (120, 120, 120)).save(root / "test" / "test (1).jpg")
    return root


def test_parse_label_file_reports_problems(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    f.write_text("0 0.5 0.5 0.2 0.2\n1 0.5 0.5 0.2 0.2\n0 0.5 0.5\n0 x 0.5 0.1 0.1\n0 0.95 0.5 0.2 0.2\n0 0.5 0.5 0 0.1\n")
    boxes, problems = parse_label_file(f, n_classes=1)
    assert len(boxes) == 4
    joined = " ".join(problems)
    for expected in ("line 2: class id 1", "line 3: expected 5", "line 4: non-numeric", "line 5: box extends", "line 6: non-positive"):
        assert expected in joined


def test_check_split_and_summary(tmp_path: Path) -> None:
    root = _yolo_dataset(tmp_path / "ds")
    splits = [check_split(root, s) for s in ("train", "val", "test")]
    s = summarise(splits)
    assert s["train"]["status"] == {"positive": 18, "no_label_file": 2}
    assert s["train"]["classes"] == ["crack"] and s["train"]["boxes"] == 18
    assert s["val"]["status"] == {"positive": 6}
    assert s["test"]["status"] == {"no_label_file": 1} and s["test"]["classes"] is None


def test_label_path_and_targets(tmp_path: Path) -> None:
    root = _yolo_dataset(tmp_path / "ds")
    assert label_path_for("train/images/train (1).jpg") == "train/labels/train (1).txt"
    recs = {r.rel_path: r for r in build_manifest(root)}
    boxes, labels = load_targets(root, recs["train/images/train (0).jpg"], 1, ["train"])
    assert boxes.shape == (1, 4) and labels.tolist() == [0]
    assert (boxes[:, 2] > boxes[:, 0]).all() and boxes.max() <= 128
    bg = load_targets(root, recs["train/images/bg (0).jpg"], 1, ["train"])
    assert bg is not None and bg[0].shape == (0, 4)
    assert load_targets(root, recs["test/test (1).jpg"], 1, ["train"]) is None


@pytest.fixture()
def detector_run(tmp_path: Path) -> Path:
    root = _yolo_dataset(tmp_path / "ds")
    records = list(build_manifest(root))
    find_duplicates(records)
    status = {}
    for r in records:
        t = load_targets(root, r, 1, ["train"])
        status[r.sample_id] = None if t is None else ("crack" if len(t[0]) else "background")
    make_group_splits(records, lambda r: status[r.sample_id], ratios={"train": 0.7, "val": 0.3, "test": 0.0},
                      seed=1, keep_duplicates_in=("train",))
    assert check_leakage(records) == []
    manifest = tmp_path / "det_manifest.jsonl"
    write_manifest(records, manifest)
    cfg = DetectionConfig(name="det_test", task="object_detection", classes=["crack"], dataset_root=str(root),
                          manifest=str(manifest), negatives_without_label_file=["train"], pretrained=False,
                          image_size=128, batch_size=4, epochs=1, warmup_iters=2, device="cpu",
                          output_dir=str(tmp_path / "runs"))
    with pytest.raises(ConfigError):
        train_detector(cfg)  # labels not verified
    return train_detector(cfg, allow_unverified_labels=True, run_name="smoke")


def test_detector_training_artefacts(detector_run: Path) -> None:
    for name in ("model.pt", "best_weights.pt", "last_weights.pt", "history.json", "val_report.json", "run.json"):
        assert (detector_run / name).is_file(), name
    run = json.loads((detector_run / "run.json").read_text())
    assert run["status"] == "completed" and run["label_status"] == "unverified"
    rep = json.loads((detector_run / "val_report.json").read_text())
    assert "map50" in rep and "image_level" in rep and rep["split"] == "val"
    ckpt = torch.load(detector_run / "model.pt", weights_only=True)
    assert ckpt["format"] == DETECTOR_FORMAT and ckpt["meta"]["classes"] == ["crack"]


def test_detector_predictor_contract(detector_run: Path, jpeg_bytes: bytes) -> None:
    p = DetectionPredictor.from_checkpoint(detector_run / "model.pt", device="cpu")
    res = p.predict(jpeg_bytes)
    payload = json.loads(json.dumps(res.to_dict()))
    validate_detection_result(payload)
    assert res.status == "ok" and res.image == {"width": 128, "height": 128}
    for d in res.detections:
        x1, y1, x2, y2 = d.bbox
        assert 0 <= x1 <= x2 <= 128 and 0 <= y1 <= y2 <= 128
        assert d.confidence >= res.score_threshold
    assert res.image_level is not None and 0 <= res.image_level["max_score"] <= 1
    assert any("unverified" in w for w in res.warnings)
    assert any("768x768" in w for w in res.warnings)
    bad = p.predict(b"")
    assert bad.status == "error" and bad.error["code"] == "empty_input" and bad.detections == []
    validate_detection_result(json.loads(json.dumps(bad.to_dict())))


def test_detector_load_errors(tmp_path: Path, detector_run: Path) -> None:
    with pytest.raises(DetectorLoadError):
        DetectionPredictor.from_checkpoint(tmp_path / "missing.pt")
    ckpt = torch.load(detector_run / "model.pt", weights_only=True)
    torch.save({**ckpt, "meta": {**ckpt["meta"], "preprocessing_version": "x"}}, tmp_path / "p.pt")
    with pytest.raises(DetectorLoadError, match="preprocessing"):
        DetectionPredictor.from_checkpoint(tmp_path / "p.pt")
    torch.save({**ckpt, "format": "other"}, tmp_path / "f.pt")
    with pytest.raises(DetectorLoadError):
        DetectionPredictor.from_checkpoint(tmp_path / "f.pt")


def test_detection_config_validation() -> None:
    cfg = DetectionConfig(name="x", task="image_classification", classes=["crack"], dataset_root=".", manifest="m")
    with pytest.raises(ConfigError):
        cfg.validate(True)
    cfg.task = "object_detection"
    cfg.arch = "yolov99"
    with pytest.raises(ConfigError):
        cfg.validate(True)
