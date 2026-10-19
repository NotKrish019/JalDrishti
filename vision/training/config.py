"""Validated experiment configuration.

Every setting that affects a run is explicit here and copied into the run directory, so an
experiment can be reproduced without undocumented state. Paths in the YAML are relative to
the repository root unless absolute.

The label gate: `labels.verified` must be true (with a written `labels.semantics` note) before
a real training run starts. Folder names are not class definitions; someone has to confirm
what each folder asserts. A pipeline smoke test may bypass the gate explicitly, and its
checkpoint is permanently marked `label_status: unverified`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

SUPPORTED_ARCHS = ("resnet18", "mobilenet_v3_small", "efficientnet_b0")
SUPPORTED_SELECTION = ("val_average_precision", "val_macro_f1", "val_balanced_accuracy", "val_loss")
REPO_ROOT = Path(__file__).resolve().parents[2]


class ConfigError(ValueError):
    pass


@dataclass
class LabelConfig:
    # Class names in index order. Must describe what the label asserts, e.g.
    # "visible_deterioration_present", never an unjustified "healthy".
    classes: List[str]
    # folder_label (top-level folder in the dataset) -> class name
    folder_to_class: Dict[str, str]
    verified: bool = False
    semantics: str = ""
    positive_class: Optional[str] = None


@dataclass
class DataConfig:
    dataset_root: str
    manifest: str
    near_duplicate_distance: int = 6
    split_seed: int = 1337
    split_ratios: Dict[str, float] = field(default_factory=lambda: {"train": 0.70, "val": 0.15, "test": 0.15})


@dataclass
class ModelConfig:
    arch: str = "resnet18"
    pretrained: bool = True
    # Documented provenance of initial weights (torchvision ImageNet-1K weights by default).
    weights_source: str = "torchvision ImageNet-1K (download.pytorch.org), BSD-3-Clause library"


@dataclass
class TrainConfig:
    image_size: int = 224
    batch_size: int = 16
    epochs: int = 15
    learning_rate: float = 3e-4
    weight_decay: float = 1e-4
    seed: int = 42
    device: str = "auto"
    num_workers: int = 2
    class_weighting: str = "inverse_frequency"  # or "none"
    early_stopping_patience: int = 4
    selection_metric: str = "val_average_precision"
    threshold_criterion: str = "f1"
    threshold_target: Optional[float] = None
    mixed_precision: bool = True  # used only on CUDA
    max_train_batches: Optional[int] = None  # bounded smoke runs
    augmentation: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperimentConfig:
    name: str
    task: str
    labels: LabelConfig
    data: DataConfig
    model: ModelConfig = field(default_factory=ModelConfig)
    train: TrainConfig = field(default_factory=TrainConfig)
    output_dir: str = "vision/outputs/experiments"

    def resolve(self, p: str) -> Path:
        path = Path(p)
        return path if path.is_absolute() else REPO_ROOT / path

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def validate(self, allow_unverified_labels: bool = False) -> None:
        if self.task != "image_classification":
            raise ConfigError(
                f"task {self.task!r} is not supported by this trainer. Detection needs verified boxes "
                "and segmentation needs verified masks; neither exists in the current dataset."
            )
        lab = self.labels
        if len(lab.classes) < 2 or len(set(lab.classes)) != len(lab.classes):
            raise ConfigError("labels.classes must list at least two distinct class names")
        bad = sorted(set(lab.folder_to_class.values()) - set(lab.classes))
        if bad:
            raise ConfigError(f"labels.folder_to_class maps to unknown classes: {bad}")
        missing = sorted(set(lab.classes) - set(lab.folder_to_class.values()))
        if missing:
            raise ConfigError(f"no folder maps to classes: {missing}")
        if any(c.lower() in ("healthy", "safe", "undamaged") for c in lab.classes) and not lab.semantics:
            raise ConfigError("a class named healthy/safe/undamaged needs an explicit labels.semantics justification")
        if lab.positive_class is not None and lab.positive_class not in lab.classes:
            raise ConfigError("labels.positive_class must be one of labels.classes")
        if not allow_unverified_labels and not (lab.verified and lab.semantics.strip()):
            raise ConfigError(
                "labels.verified is false (or labels.semantics is empty). Confirm what each folder "
                "asserts before training; pass --allow-unverified-labels only for a pipeline smoke test."
            )
        if self.model.arch not in SUPPORTED_ARCHS:
            raise ConfigError(f"model.arch must be one of {SUPPORTED_ARCHS}")
        t = self.train
        if t.selection_metric not in SUPPORTED_SELECTION:
            raise ConfigError(f"train.selection_metric must be one of {SUPPORTED_SELECTION}")
        if t.selection_metric == "val_average_precision" and len(lab.classes) != 2:
            raise ConfigError("val_average_precision applies to binary tasks only")
        if not 32 <= t.image_size <= 1024 or t.batch_size < 1 or t.epochs < 1 or t.learning_rate <= 0:
            raise ConfigError("train.image_size/batch_size/epochs/learning_rate out of range")
        if t.class_weighting not in ("inverse_frequency", "none"):
            raise ConfigError("train.class_weighting must be inverse_frequency or none")
        if t.device not in ("auto", "cpu", "cuda", "mps") and not t.device.startswith("cuda:"):
            raise ConfigError("train.device must be auto, cpu, cuda, cuda:N or mps")
        if abs(sum(self.data.split_ratios.values()) - 1) > 1e-6:
            raise ConfigError("data.split_ratios must sum to 1")


def load_config(path: Path | str) -> ExperimentConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    try:
        return ExperimentConfig(
            name=raw["name"],
            task=raw["task"],
            labels=LabelConfig(**raw["labels"]),
            data=DataConfig(**raw["data"]),
            model=ModelConfig(**raw.get("model", {})),
            train=TrainConfig(**raw.get("train", {})),
            output_dir=raw.get("output_dir", "vision/outputs/experiments"),
        )
    except (KeyError, TypeError) as exc:
        raise ConfigError(f"invalid config {path}: {exc}") from exc
