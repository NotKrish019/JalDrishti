"""
Jaldrishti - Crack Detection Training Sprint (YOLOv8n)
Emergency Hackathon MVP Pilot
"""

import os
import sys
import time
from pathlib import Path
from ultralytics import YOLO

def main():
    print("=" * 60)
    print("JALDRISHTI — CRACK DETECTION PILOT TRAINING (YOLOv8n)")
    print("=" * 60)

    project_root = Path(__file__).resolve().parent.parent.parent
    data_yaml = project_root / "data" / "processed" / "crack_pilot" / "data.yaml"
    output_dir = project_root / "vision" / "outputs" / "train"

    if not data_yaml.exists():
        print(f"ERROR: Dataset config not found at {data_yaml}")
        sys.exit(1)

    print(f"Data config: {data_yaml}")
    print(f"Output directory: {output_dir}")

    # Use yolov8n.pt
    model_name = "yolov8n.pt"
    print(f"Initializing YOLO model: {model_name}...")
    model = YOLO(model_name)

    # Training configuration per emergency sprint specs
    imgsz = 512
    batch = 4
    epochs = 5
    device = 0

    print(f"Training config: imgsz={imgsz}, batch={batch}, epochs={epochs}, device={device}")
    start_time = time.time()

    try:
        results = model.train(
            data=str(data_yaml),
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            device=device,
            project=str(output_dir),
            name="crack_pilot",
            exist_ok=True,
            verbose=True,
            workers=0,
            plots=False,
            save=True
        )
    except Exception as e:
        print(f"Training failed with batch={batch}: {e}")
        print("Retrying with batch=2...")
        results = model.train(
            data=str(data_yaml),
            epochs=epochs,
            imgsz=imgsz,
            batch=2,
            device=device,
            project=str(output_dir),
            name="crack_pilot",
            exist_ok=True,
            verbose=True,
            workers=0,
            plots=False,
            save=True
        )

    elapsed_time = time.time() - start_time
    print("=" * 60)
    print(f"TRAINING COMPLETE in {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
    
    # Check best model path
    best_pt = output_dir / "crack_pilot" / "weights" / "best.pt"
    if best_pt.exists():
        print(f"Best checkpoint saved at: {best_pt} ({best_pt.stat().st_size / 1024 / 1024:.2f} MB)")
    else:
        last_pt = output_dir / "crack_pilot" / "weights" / "last.pt"
        print(f"Last checkpoint saved at: {last_pt}")

    # Run validation
    print("\nRunning Validation...")
    metrics = model.val()
    print(f"Validation mAP50: {metrics.box.map50:.4f}")
    print(f"Validation mAP50-95: {metrics.box.map:.4f}")
    print("=" * 60)

if __name__ == "__main__":
    main()
