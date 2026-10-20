"""
Jaldrishti - Visual Vegetation Indicator (Deterministic OpenCV)
Emergency Hackathon MVP Feature

IMPORTANT NOTICE:
This module is a deterministic OpenCV-based visual indicator, NOT an AI model.
It estimates vegetation/algal/moss coverage on heritage masonry surfaces
using color-space thresholding (HSV) and morphological operations.
It does NOT perform species classification or structural safety certification.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

def analyze_vegetation_indicator(
    image_input: Any,
    min_coverage_threshold: float = 0.005,
    save_overlay_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Computes a deterministic visual vegetation indicator on stone/brick masonry.
    
    Args:
        image_input: File path (str/Path) or numpy BGR image array.
        min_coverage_threshold: Coverage ratio threshold to flag detected=True.
        save_overlay_path: Optional path to save visual overlay.
        
    Returns:
        dict: {
            "visual_indicator": bool,
            "coverage_ratio": float,
            "pixel_count": int,
            "total_pixels": int
        }
    """
    if isinstance(image_input, (str, Path)):
        img = cv2.imread(str(image_input))
        if img is None:
            raise FileNotFoundError(f"Could not load image from {image_input}")
    else:
        img = image_input

    h, w = img.shape[:2]
    total_pixels = h * w

    # 1. Convert BGR to HSV color space
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 2. Green-hue threshold range for heritage foliage, moss, and algae
    # Hue: ~28 to 90 (yellow-green to dark emerald)
    # Saturation: 30 to 255
    # Value: 30 to 255
    lower_green = np.array([28, 30, 30], dtype=np.uint8)
    upper_green = np.array([90, 255, 255], dtype=np.uint8)
    green_mask = cv2.inRange(hsv, lower_green, upper_green)

    # 3. Morphological cleanup (eliminate single-pixel noise, fill minor holes)
    kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    cleaned_mask = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, kernel_open)
    cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_CLOSE, kernel_close)

    # 4. Filter out very small isolated components (< 50 pixels)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(cleaned_mask, connectivity=8)
    filtered_mask = np.zeros_like(cleaned_mask)
    min_area = 50

    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] >= min_area:
            filtered_mask[labels == i] = 255

    # 5. Coverage calculation
    vegetation_pixels = int(np.count_nonzero(filtered_mask))
    coverage_ratio = round(float(vegetation_pixels) / float(total_pixels), 4)
    indicator_present = coverage_ratio >= min_coverage_threshold

    # 6. Optional visualization overlay
    if save_overlay_path:
        overlay = img.copy()
        # Highlight vegetation in vibrant green alpha tint
        green_tint = np.zeros_like(img)
        green_tint[:, :] = [0, 220, 0] # BGR
        
        mask_3ch = cv2.cvtColor(filtered_mask, cv2.COLOR_GRAY2BGR)
        tinted = np.where(mask_3ch > 0, cv2.addWeighted(img, 0.4, green_tint, 0.6, 0), img)
        
        # Add informative label
        label_text = f"Vegetation Indicator: {coverage_ratio*100:.1f}% coverage"
        cv2.putText(tinted, label_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
        
        out_p = Path(save_overlay_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out_p), tinted)

    return {
        "visual_indicator": indicator_present,
        "coverage_ratio": coverage_ratio,
        "pixel_count": vegetation_pixels,
        "total_pixels": total_pixels
    }

if __name__ == "__main__":
    # Smoke test on a synthetic image
    test_img = np.zeros((200, 200, 3), dtype=np.uint8)
    test_img[50:150, 50:150] = [34, 139, 34] # Forest Green in BGR: (34, 139, 34)
    result = analyze_vegetation_indicator(test_img)
    print("Vegetation Indicator Smoke Test Result:", result)
    assert result["visual_indicator"] is True
    print("Smoke test PASSED!")
