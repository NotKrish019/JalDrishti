"""Classifier backbones from torchvision, with the final layer sized to the task."""

from __future__ import annotations

from typing import Tuple


def build_classifier(arch: str, num_classes: int, pretrained: bool):
    """Return (model, weights_id). Pretrained weights come from torchvision's official
    ImageNet-1K checkpoints and are downloaded by torchvision on first use."""
    import torch.nn as nn
    from torchvision import models

    if arch == "resnet18":
        weights = models.ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
        m = models.resnet18(weights=weights)
        m.fc = nn.Linear(m.fc.in_features, num_classes)
    elif arch == "mobilenet_v3_small":
        weights = models.MobileNet_V3_Small_Weights.IMAGENET1K_V1 if pretrained else None
        m = models.mobilenet_v3_small(weights=weights)
        m.classifier[-1] = nn.Linear(m.classifier[-1].in_features, num_classes)
    elif arch == "efficientnet_b0":
        weights = models.EfficientNet_B0_Weights.IMAGENET1K_V1 if pretrained else None
        m = models.efficientnet_b0(weights=weights)
        m.classifier[-1] = nn.Linear(m.classifier[-1].in_features, num_classes)
    else:
        raise ValueError(f"unsupported arch {arch!r}")
    return m, (str(weights) if weights else "random_init")


def select_device(preference: str = "auto") -> Tuple[object, str]:
    """Return (torch.device, description). auto: CUDA, then Apple MPS, then CPU."""
    import torch

    if preference == "auto":
        if torch.cuda.is_available():
            preference = "cuda"
        elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            preference = "mps"
        else:
            preference = "cpu"
    if preference.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but not available")
    if preference == "mps" and not torch.backends.mps.is_available():
        raise RuntimeError("MPS requested but not available")
    device = torch.device(preference)
    if device.type == "cuda":
        idx = device.index or 0
        desc = f"cuda:{idx} {torch.cuda.get_device_name(idx)}"
    elif device.type == "mps":
        desc = "mps (Apple GPU)"
    else:
        desc = "cpu"
    return device, desc
