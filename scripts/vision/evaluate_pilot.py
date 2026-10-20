"""
Jaldrishti - Vision Pilot Inference & Demo Pipeline
Performs unseen image testing, computes unified output contract,
and exports demo samples to vision/outputs/demo/.
"""

import os
import sys
import json
import shutil
from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO

# Import local vegetation indicator
sys.path.insert(0, str(Path(__file__).resolve().parent))
from vegetation_indicator import analyze_vegetation_indicator

def run_evaluation_and_demo():
    print("=" * 60)
    print("JALDRISHTI — VISION PILOT EVALUATION & DEMO GENERATION")
    print("=" * 60)

    project_root = Path(__file__).resolve().parent.parent.parent
    best_weights = project_root / "vision" / "outputs" / "train" / "crack_pilot" / "weights" / "best.pt"
    
    if not best_weights.exists():
        # Fallback to last.pt or yolov8n.pt if best.pt not generated yet
        last_weights = project_root / "vision" / "outputs" / "train" / "crack_pilot" / "weights" / "last.pt"
        if last_weights.exists():
            best_weights = last_weights
        else:
            print(f"Warning: Model weights not found at {best_weights}. Looking for yolov8n.pt...")
            best_weights = project_root / "yolov8n.pt"
            if not best_weights.exists():
                print("Error: No weights available.")
                sys.exit(1)

    print(f"Loading weights from: {best_weights}")
    model = YOLO(str(best_weights))

    damaged_dir = project_root / "Darbhanga_Fort" / "Darbhanga_Fort" / "Damaged_images"
    bg_dir = project_root / "Darbhanga_Fort" / "Darbhanga_Fort" / "Background_images"
    demo_dir = project_root / "vision" / "outputs" / "demo"
    demo_dir.mkdir(parents=True, exist_ok=True)

    # Pick 5-10 UNSEEN images (indices not in pilot train/val splits: 1-16)
    crack_samples = [
        damaged_dir / "0 (20).jpg",
        damaged_dir / "0 (25).jpg",
        damaged_dir / "0 (30).jpg",
        damaged_dir / "0 (35).jpg",
        damaged_dir / "0 (40).jpg",
    ]
    bg_samples = [
        bg_dir / "ND (20).jpg",
        bg_dir / "ND (25).jpg",
        bg_dir / "ND (30).jpg",
        bg_dir / "ND (35).jpg",
    ]

    all_test_images = [p for p in (crack_samples + bg_samples) if p.exists()]
    print(f"Found {len(all_test_images)} unseen test images.")

    eval_results = []
    crack_positive_demos = 0
    bg_demos = 0
    veg_demos = 0

    for img_path in all_test_images:
        is_bg = "ND" in img_path.name
        img_bgr = cv2.imread(str(img_path))
        if img_bgr is None:
            continue

        h, w = img_bgr.shape[:2]

        # 1. Run Crack Detection
        yolo_res = model.predict(source=str(img_path), conf=0.25, imgsz=512, verbose=False)[0]
        
        detected_crack = len(yolo_res.boxes) > 0
        best_box = None
        best_conf = 0.0

        if detected_crack:
            # Pick highest confidence detection
            best_idx = int(yolo_res.boxes.conf.argmax())
            best_conf = float(yolo_res.boxes.conf[best_idx])
            xyxy = yolo_res.boxes.xyxy[best_idx].cpu().numpy().tolist()
            best_box = [round(float(c), 1) for c in xyxy]

        # 2. Run Deterministic Vegetation Visual Indicator
        veg_info = analyze_vegetation_indicator(img_bgr)

        # 3. Build Unified Output Contract
        contract = {
            "image": img_path.name,
            "type": "background" if is_bg else "damaged_masonry",
            "crack": {
                "detected": detected_crack,
                "confidence": round(best_conf, 2),
                "bbox": best_box
            },
            "vegetation": {
                "visual_indicator": veg_info["visual_indicator"],
                "coverage_ratio": veg_info["coverage_ratio"]
            }
        }
        eval_results.append(contract)

        # 4. Prepare Visual Overlay for Demo
        annotated_img = img_bgr.copy()

        # Draw crack bounding box
        if detected_crack and best_box is not None:
            x1, y1, x2, y2 = [int(v) for v in best_box]
            cv2.rectangle(annotated_img, (x1, y1), (x2, y2), (0, 0, 230), 3) # Red box
            label = f"Crack {best_conf:.2f}"
            cv2.putText(annotated_img, label, (x1, max(25, y1 - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 230), 2, cv2.LINE_AA)

        # Draw vegetation badge if present
        if veg_info["visual_indicator"]:
            veg_label = f"Veg Indicator: {veg_info['coverage_ratio']*100:.1f}%"
            cv2.putText(annotated_img, veg_label, (15, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 0), 2, cv2.LINE_AA)
        else:
            cv2.putText(annotated_img, "Masonry Clean", (15, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2, cv2.LINE_AA)

        # Save demo items
        stem = img_path.stem
        # Save originals and overlays
        if not is_bg and detected_crack and crack_positive_demos < 3:
            crack_positive_demos += 1
            shutil.copy2(img_path, demo_dir / f"crack_{crack_positive_demos}_orig.jpg")
            cv2.imwrite(str(demo_dir / f"crack_{crack_positive_demos}_pred.jpg"), annotated_img)

        elif is_bg and bg_demos < 2:
            bg_demos += 1
            shutil.copy2(img_path, demo_dir / f"bg_{bg_demos}_orig.jpg")
            cv2.imwrite(str(demo_dir / f"bg_{bg_demos}_pred.jpg"), annotated_img)

        if veg_info["visual_indicator"] and veg_demos < 2:
            veg_demos += 1
            shutil.copy2(img_path, demo_dir / f"veg_{veg_demos}_orig.jpg")
            cv2.imwrite(str(demo_dir / f"veg_{veg_demos}_pred.jpg"), annotated_img)

    # Save summary json
    summary_path = demo_dir / "evaluation_summary.json"
    with open(summary_path, "w") as f:
        json.dump(eval_results, f, indent=2)

    print("\nEvaluation completed. Results summary:")
    print(json.dumps(eval_results, indent=2))
    print(f"\nSaved evaluation summary to: {summary_path}")
    print(f"Saved demo cases to: {demo_dir}")

if __name__ == "__main__":
    run_evaluation_and_demo()
