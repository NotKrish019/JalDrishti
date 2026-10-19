"""Config gate, a bounded CPU training run on synthetic data, and the predictor contract.

The training run here proves the pipeline works end to end; its numbers mean nothing about
real damage (the data is synthetic and the labels are deliberately marked unverified).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("torchvision")

from vision.data.duplicates import find_duplicates  # noqa: E402
from vision.data.manifest import build_manifest, write_manifest  # noqa: E402
from vision.data.splits import check_leakage, make_group_splits  # noqa: E402
from vision.inference.predictor import ImageClassifierPredictor, ModelLoadError  # noqa: E402
from vision.inference.schema import CHECKPOINT_FORMAT, validate_result  # noqa: E402
from vision.training.config import (  # noqa: E402
    ConfigError,
    DataConfig,
    ExperimentConfig,
    LabelConfig,
    ModelConfig,
    TrainConfig,
    load_config,
)

CLASSES = ["background_folder_unconfirmed", "visible_deterioration_folder"]
FOLDERS = {"Background_images": CLASSES[0], "Damaged_images": CLASSES[1]}
REPO = Path(__file__).resolve().parents[2]


def _config(root: Path, manifest: Path, out: Path, verified: bool = False) -> ExperimentConfig:
    return ExperimentConfig(
        name="test_pilot",
        task="image_classification",
        labels=LabelConfig(classes=CLASSES, folder_to_class=FOLDERS, positive_class=CLASSES[1],
                           verified=verified, semantics="synthetic test labels" if verified else ""),
        data=DataConfig(dataset_root=str(root), manifest=str(manifest)),
        model=ModelConfig(arch="mobilenet_v3_small", pretrained=False),
        train=TrainConfig(image_size=64, batch_size=8, epochs=2, device="cpu", num_workers=0,
                          early_stopping_patience=5, learning_rate=1e-3),
        output_dir=str(out),
    )


def test_repository_pilot_config_is_valid_but_gated() -> None:
    cfg = load_config(REPO / "vision" / "configs" / "classification_pilot.yaml")
    cfg.validate(allow_unverified_labels=True)
    with pytest.raises(ConfigError, match="verified"):
        cfg.validate()
    assert not any(c in ("healthy", "undamaged") for c in cfg.labels.classes)


def test_config_rejects_unsupported_tasks_and_bad_mappings(tmp_path: Path) -> None:
    cfg = _config(tmp_path, tmp_path / "m.jsonl", tmp_path, verified=True)
    cfg.task = "segmentation"
    with pytest.raises(ConfigError, match="masks"):
        cfg.validate()
    cfg = _config(tmp_path, tmp_path / "m.jsonl", tmp_path, verified=True)
    cfg.labels.folder_to_class = {"Background_images": "nope", "Damaged_images": CLASSES[1]}
    with pytest.raises(ConfigError):
        cfg.validate()
    cfg = _config(tmp_path, tmp_path / "m.jsonl", tmp_path, verified=True)
    cfg.labels.classes = ["healthy", CLASSES[1]]
    cfg.labels.folder_to_class = {"Background_images": "healthy", "Damaged_images": CLASSES[1]}
    cfg.labels.semantics = ""
    with pytest.raises(ConfigError):
        cfg.validate(allow_unverified_labels=True)


@pytest.fixture()
def trained_run(synthetic_dataset: Path, tmp_path: Path) -> Path:
    from vision.training.classifier import train

    records = list(build_manifest(synthetic_dataset))
    find_duplicates(records)
    make_group_splits(records, FOLDERS, ratios={"train": 0.6, "val": 0.4, "test": 0.0}, seed=3)
    assert check_leakage(records) == []
    manifest = tmp_path / "manifest_split.jsonl"
    write_manifest(records, manifest)
    cfg = _config(synthetic_dataset, manifest, tmp_path / "runs")
    with pytest.raises(ConfigError):
        train(cfg)  # unverified labels are refused for real runs
    return train(cfg, allow_unverified_labels=True, run_name="smoke")


def test_training_run_writes_reproducible_artefacts(trained_run: Path) -> None:
    for name in ("model.pt", "best_weights.pt", "last_weights.pt", "history.json", "val_report.json", "run.json"):
        assert (trained_run / name).is_file(), name
    run = json.loads((trained_run / "run.json").read_text())
    assert run["status"] == "completed"
    assert run["label_status"] == "unverified"
    assert run["config"]["train"]["seed"] == 42
    assert "torch" in run["versions"] and len(run["manifest_sha256"]) == 64
    history = json.loads((trained_run / "history.json").read_text())
    assert 1 <= len(history) <= 2
    report = json.loads((trained_run / "val_report.json").read_text())
    assert report["decision"]["rule"] in ("threshold", "argmax")
    assert sum(sum(r) for r in report["confusion_matrix"]) == report["n_samples"]


def test_run_directory_is_never_overwritten(trained_run: Path, synthetic_dataset: Path) -> None:
    from vision.training.classifier import train

    cfg = _config(synthetic_dataset, Path(json.loads((trained_run / "run.json").read_text())["config"]["data"]["manifest"]),
                  trained_run.parents[1])
    with pytest.raises(FileExistsError):
        train(cfg, allow_unverified_labels=True, run_name="smoke")


def test_predictor_output_matches_contract(trained_run: Path, jpeg_bytes: bytes) -> None:
    p = ImageClassifierPredictor.from_checkpoint(trained_run / "model.pt", device="cpu")
    res = p.predict(jpeg_bytes)
    payload = res.to_dict()
    validate_result(json.loads(json.dumps(payload)))
    assert res.status == "ok"
    assert [s.class_name for s in res.predictions] and {s.class_name for s in res.predictions} == set(CLASSES)
    assert sum(s.score for s in res.predictions) == pytest.approx(1.0, abs=1e-5)
    assert res.predictions[0].score >= res.predictions[1].score
    assert res.image == {"width": 128, "height": 128}
    assert res.label_status == "unverified" and any("unverified" in w for w in res.warnings)
    assert "bbox" not in json.dumps(payload) and "mask" not in json.dumps(payload)
    if res.decision is not None:
        assert res.decision["positive_class"] == CLASSES[1]
        assert 0.0 <= res.decision["threshold"] <= 1.0


def test_predictor_is_deterministic(trained_run: Path, jpeg_bytes: bytes) -> None:
    p = ImageClassifierPredictor.from_checkpoint(trained_run / "model.pt", device="cpu")
    a = [s.score for s in p.predict(jpeg_bytes).predictions]
    b = [s.score for s in p.predict(jpeg_bytes).predictions]
    assert a == b


@pytest.mark.parametrize("payload,code", [(b"", "empty_input"), (b"garbage", "unreadable_image"), ("missing.jpg", "not_found")])
def test_predictor_reports_bad_input_as_structured_error(trained_run: Path, payload, code) -> None:
    p = ImageClassifierPredictor.from_checkpoint(trained_run / "model.pt", device="cpu")
    res = p.predict(payload)
    assert res.status == "error" and res.error["code"] == code and res.predictions == []
    validate_result(json.loads(res.to_json()))


def test_predictor_load_failures(tmp_path: Path, trained_run: Path) -> None:
    with pytest.raises(ModelLoadError, match="not found"):
        ImageClassifierPredictor.from_checkpoint(tmp_path / "nope.pt")
    (tmp_path / "junk.pt").write_bytes(b"not a checkpoint")
    with pytest.raises(ModelLoadError):
        ImageClassifierPredictor.from_checkpoint(tmp_path / "junk.pt")
    ckpt = torch.load(trained_run / "model.pt", weights_only=True)
    torch.save({**ckpt, "format": "something-else"}, tmp_path / "wrong_format.pt")
    with pytest.raises(ModelLoadError, match="not a"):
        ImageClassifierPredictor.from_checkpoint(tmp_path / "wrong_format.pt")
    bad = {**ckpt, "meta": {**ckpt["meta"], "classes": ["only_one"]}}
    torch.save(bad, tmp_path / "bad_classes.pt")
    with pytest.raises(ModelLoadError, match="class mapping"):
        ImageClassifierPredictor.from_checkpoint(tmp_path / "bad_classes.pt")
    prep = {**ckpt, "meta": {**ckpt["meta"], "preprocessing_version": "old"}}
    torch.save(prep, tmp_path / "prep.pt")
    with pytest.raises(ModelLoadError, match="preprocessing"):
        ImageClassifierPredictor.from_checkpoint(tmp_path / "prep.pt")
    assert ckpt["format"] == CHECKPOINT_FORMAT


def test_mps_or_cuda_smoke_when_available(trained_run: Path, jpeg_bytes: bytes) -> None:
    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        pytest.skip("no GPU backend on this machine")
    cpu = ImageClassifierPredictor.from_checkpoint(trained_run / "model.pt", device="cpu").predict(jpeg_bytes)
    gpu = ImageClassifierPredictor.from_checkpoint(trained_run / "model.pt", device=device).predict(jpeg_bytes)
    assert gpu.status == "ok"
    np.testing.assert_allclose([s.score for s in cpu.predictions], [s.score for s in gpu.predictions], atol=1e-3)
