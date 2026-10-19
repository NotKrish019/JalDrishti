"""Measure single-image inference latency of the classifier pipeline.

    python3 scripts/vision/benchmark_inference.py --checkpoint <run_dir>/model.pt --device auto
    python3 scripts/vision/benchmark_inference.py --random-init --arch resnet18 --device cpu

Stages are timed separately (load, preprocess, forward, postprocess) after a warm-up, with
device synchronisation for CUDA/MPS. Timings exclude disk I/O: the input is decoded from bytes
already in memory. `--random-init` measures architecture runtime only; it says nothing about
accuracy and the output is not a trained Jaldrishti model.
"""

from __future__ import annotations

import argparse
import io
import json
import statistics
import sys
import tempfile
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _sync(device) -> None:
    import torch

    if device.type == "cuda":
        torch.cuda.synchronize(device)
    elif device.type == "mps":
        torch.mps.synchronize()


def _random_checkpoint(arch: str, image_size: int, path: Path) -> None:
    import torch

    from vision.inference.schema import CHECKPOINT_FORMAT
    from vision.preprocessing.transforms import PREPROCESSING_VERSION
    from vision.training.backbones import build_classifier

    model, _ = build_classifier(arch, 2, pretrained=False)
    torch.save({
        "format": CHECKPOINT_FORMAT,
        "state_dict": model.state_dict(),
        "meta": {"model_name": f"benchmark-{arch}-random-init", "model_version": "random-init",
                 "task_type": "image_classification", "arch": arch, "classes": ["class_0", "class_1"],
                 "image_size": image_size, "preprocessing_version": PREPROCESSING_VERSION,
                 "label_status": "unverified"},
    }, path)


def _pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))]


def main() -> int:
    import numpy as np
    import torch
    from PIL import Image

    from vision.inference.predictor import ImageClassifierPredictor
    from vision.preprocessing.transforms import load_image, to_model_tensor

    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", default=None)
    ap.add_argument("--random-init", action="store_true")
    ap.add_argument("--arch", default="resnet18")
    ap.add_argument("--image-size", type=int, default=224)
    ap.add_argument("--input-size", type=int, default=768, help="side of the synthetic input image")
    ap.add_argument("--image", default=None, help="optional real image to use instead of a synthetic one")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--warmup", type=int, default=10)
    ap.add_argument("--reps", type=int, default=100)
    args = ap.parse_args()

    tmp = None
    ckpt = args.checkpoint
    if args.random_init:
        tmp = tempfile.TemporaryDirectory()
        ckpt = str(Path(tmp.name) / "random.pt")
        _random_checkpoint(args.arch, args.image_size, Path(ckpt))
    if not ckpt:
        print("pass --checkpoint or --random-init", file=sys.stderr)
        return 2

    t0 = time.perf_counter()
    predictor = ImageClassifierPredictor.from_checkpoint(ckpt, device=args.device)
    load_ms = (time.perf_counter() - t0) * 1000
    dev = predictor.device
    size = int(predictor.meta["image_size"])

    if args.image:
        data = Path(args.image).read_bytes()
    else:
        rng = np.random.default_rng(0)
        buf = io.BytesIO()
        Image.fromarray(rng.integers(0, 255, (args.input_size, args.input_size, 3), dtype=np.uint8)).save(buf, "JPEG", quality=90)
        data = buf.getvalue()

    pre, fwd, post = [], [], []
    with torch.inference_mode():
        for i in range(args.warmup + args.reps):
            a = time.perf_counter()
            x = to_model_tensor(load_image(data), size).unsqueeze(0).to(dev)
            _sync(dev)
            b = time.perf_counter()
            logits = predictor.model(x)
            _sync(dev)
            c = time.perf_counter()
            torch.softmax(logits.float(), dim=1)[0].cpu().tolist()
            d = time.perf_counter()
            if i >= args.warmup:
                pre.append((b - a) * 1000)
                fwd.append((c - b) * 1000)
                post.append((d - c) * 1000)
    total = [p + f + q for p, f, q in zip(pre, fwd, post)]

    def stats(xs):
        return {"median": statistics.median(xs), "p90": _pct(xs, 0.9), "p99": _pct(xs, 0.99), "max": max(xs)}

    import platform

    result = {
        "model": predictor.meta["model_name"],
        "weights": "random initialisation (runtime only)" if args.random_init else predictor.meta["model_version"],
        "arch": predictor.meta["arch"],
        "device": predictor.device_desc,
        "host": f"{platform.machine()} {platform.platform()}",
        "torch": torch.__version__,
        "model_input": f"{size}x{size}",
        "source_image": f"{args.input_size}x{args.input_size} synthetic JPEG" if not args.image else Path(args.image).name,
        "batch_size": 1,
        "warmup": args.warmup,
        "repetitions": args.reps,
        "includes_disk_io": False,
        "model_load_ms": load_ms,
        "preprocess_ms": stats(pre),
        "forward_ms": stats(fwd),
        "postprocess_ms": stats(post),
        "total_per_image_ms": stats(total),
    }
    print(json.dumps(result, indent=2))
    if tmp:
        tmp.cleanup()
    return 0


if __name__ == "__main__":
    sys.exit(main())
