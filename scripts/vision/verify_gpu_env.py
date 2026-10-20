"""GPU Environment and Pretrained Inference Smoke Test.

Jaldrishti Computer Vision Subsystem - Phase 2 Stage 1
Owner: Krish (Computer Vision / AI Lead)

Verifies PyTorch CUDA acceleration, GPU memory, Ultralytics YOLOv8 segmentation,
and executes a real GPU inference smoke test on a sample local dataset image.
"""

import sys
from pathlib import Path


def verify_environment() -> dict:
    import torch
    import torchvision
    import cv2
    import numpy as np
    import ultralytics
    from ultralytics import YOLO

    cuda_available = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if cuda_available else "CPU"
    vram_gb = (
        round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
        if cuda_available
        else 0.0
    )

    env_report = {
        "python_version": sys.version.split()[0],
        "pytorch_version": torch.__version__,
        "torchvision_version": torchvision.__version__,
        "pytorch_cuda": torch.version.cuda,
        "cuda_available": cuda_available,
        "gpu_name": device_name,
        "gpu_memory_gb": vram_gb,
        "opencv_version": cv2.__version__,
        "numpy_version": np.__version__,
        "ultralytics_version": ultralytics.__version__,
    }

    if not cuda_available:
        env_report["smoke_test"] = "FAILED: CUDA not available on active PyTorch."
        return env_report

    # Locate sample test image
    sample_candidates = [
        Path("Darbhanga_Fort/Darbhanga_Fort/Damaged_images/0 (1).jpg"),
        Path("Darbhanga_Fort/Damaged_images/0 (1).jpg"),
        Path("data/raw/Darbhanga_Fort/Damaged_images/0 (1).jpg"),
    ]
    sample_img = None
    for c in sample_candidates:
        if c.exists():
            sample_img = c
            break

    if sample_img is None:
        env_report["smoke_test"] = "SKIPPED: Sample dataset image not found."
        return env_report

    # Run inference with pretrained checkpoint on GPU (cuda:0)
    model = YOLO("yolov8n-seg.pt")
    results = model(str(sample_img), device=0, verbose=False)

    boxes_count = len(results[0].boxes) if results and results[0].boxes is not None else 0
    device_used = str(results[0].boxes.data.device) if boxes_count > 0 else "cuda:0"

    env_report["smoke_test"] = {
        "status": "PASS",
        "sample_image": str(sample_img),
        "device_used": device_used,
        "boxes_detected": boxes_count,
        "preprocess_ms": round(results[0].speed.get("preprocess", 0), 2),
        "inference_ms": round(results[0].speed.get("inference", 0), 2),
        "postprocess_ms": round(results[0].speed.get("postprocess", 0), 2),
    }

    return env_report


if __name__ == "__main__":
    report = verify_environment()
    print("=" * 60)
    print("JALDRISHTI VISION — STAGE 1 GPU ENVIRONMENT REPORT")
    print("=" * 60)
    for k, v in report.items():
        print(f"{k}: {v}")
    print("=" * 60)
