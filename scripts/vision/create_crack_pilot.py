"""Generates minimal YOLO crack detection pilot dataset with hard negatives.

BaoliGuard Vision - Emergency Phase 2 Sprint
Owner: Krish (Computer Vision / AI Lead)

LEGACY. The boxes written here come from an OpenCV black-hat heuristic (with a fixed centre
box as fallback), not from human annotation, so a detector trained on them learns to imitate
the heuristic. Kept for traceability of vision/models/crack_pilot_yolov8n.pt; see
vision/docs/MODEL_CARD_crack_pilot_v0.md. New work uses vision/ and scripts/vision/train_classifier.py.
"""

import os
import shutil
from pathlib import Path
import cv2
import numpy as np


def extract_crack_boxes(img_path: str, max_boxes: int = 3) -> list[tuple[float, float, float, float]]:
    """Extracts dominant crack bounding boxes in normalized YOLO format (xc, yc, w, h)."""
    img = cv2.imread(img_path)
    if img is None:
        return []
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (7, 7), 0)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    blackhat = cv2.morphologyEx(blur, cv2.MORPH_BLACKHAT, kernel)
    _, thresh = cv2.threshold(blackhat, 22, 255, cv2.THRESH_BINARY)
    dilated = cv2.dilate(thresh, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)), iterations=2)
    cnts, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:max_boxes]

    yolo_boxes = []
    for c in cnts:
        if cv2.contourArea(c) < 800:
            continue
        bx, by, bw, bh = cv2.boundingRect(c)
        # Pad box slightly
        pad = 6
        bx = max(0, bx - pad)
        by = max(0, by - pad)
        bw = min(w - bx, bw + 2 * pad)
        bh = min(h - by, bh + 2 * pad)

        xc = (bx + bw / 2.0) / w
        yc = (by + bh / 2.0) / h
        norm_w = bw / float(w)
        norm_h = bh / float(h)
        yolo_boxes.append((round(xc, 5), round(yc, 5), round(norm_w, 5), round(norm_h, 5)))

    # Fallback to center-focused inspection box if none met area threshold
    if not yolo_boxes:
        yolo_boxes.append((0.5, 0.5, 0.4, 0.4))

    return yolo_boxes


def build_crack_pilot_dataset(output_dir: str = "data/processed/crack_pilot") -> dict:
    base_damaged = Path("Darbhanga_Fort/Darbhanga_Fort/Damaged_images")
    base_bg = Path("Darbhanga_Fort/Darbhanga_Fort/Background_images")

    out_path = Path(output_dir)
    for split in ["train", "val"]:
        (out_path / "images" / split).mkdir(parents=True, exist_ok=True)
        (out_path / "labels" / split).mkdir(parents=True, exist_ok=True)

    # Select 16 damaged and 16 background files
    damaged_files = sorted(list(base_damaged.glob("*.jpg")))[:16]
    bg_files = sorted(list(base_bg.glob("*.jpg")))[:16]

    train_damaged = damaged_files[:12]
    val_damaged = damaged_files[12:16]

    train_bg = bg_files[:12]
    val_bg = bg_files[12:16]

    stats = {"train_crack": 0, "val_crack": 0, "train_bg": 0, "val_bg": 0}

    # Process crack images
    for split, img_list in [("train", train_damaged), ("val", val_damaged)]:
        for img_file in img_list:
            dest_img = out_path / "images" / split / img_file.name
            shutil.copy2(img_file, dest_img)

            boxes = extract_crack_boxes(str(img_file))
            dest_lbl = out_path / "labels" / split / f"{img_file.stem}.txt"
            with open(dest_lbl, "w") as f:
                for xc, yc, bw, bh in boxes:
                    f.write(f"0 {xc} {yc} {bw} {bh}\n")
            stats[f"{split}_crack"] += 1

    # Process background images (empty label files for hard negatives)
    for split, img_list in [("train", train_bg), ("val", val_bg)]:
        for img_file in img_list:
            dest_img = out_path / "images" / split / img_file.name
            shutil.copy2(img_file, dest_img)

            dest_lbl = out_path / "labels" / split / f"{img_file.stem}.txt"
            dest_lbl.write_text("")  # Empty label for background
            stats[f"{split}_bg"] += 1

    # Write data.yaml
    yaml_content = f"""path: {out_path.resolve().as_posix()}
train: images/train
val: images/val

names:
  0: crack
"""
    (out_path / "data.yaml").write_text(yaml_content)
    return stats


if __name__ == "__main__":
    s = build_crack_pilot_dataset()
    print("Crack pilot dataset generated:", s)
