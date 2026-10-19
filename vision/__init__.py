"""JalDrishti vision subsystem (SEE stage).

Owner: Krish (Computer Vision / AI).

Subpackages:
    data           dataset manifest, duplicate detection, leakage-safe splits, contact sheets
    preprocessing  image validation and the versioned inference/training transforms
    metrics        task-specific evaluation (image classification)
    training       configuration and the reproducible classifier training loop
    inference      the predictor and its structured, documented output contract

Model outputs are candidate observations for human review. Nothing in this package
establishes structural safety, material chemistry, groundwater condition or a repair method.
"""

__all__ = ["data", "preprocessing", "metrics", "training", "inference"]
