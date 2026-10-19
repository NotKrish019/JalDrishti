"""Dataset auditing, duplicate detection and leakage-safe splitting."""

from vision.data.manifest import (
    ANNOTATION_EXTENSIONS,
    IMAGE_EXTENSIONS,
    ImageRecord,
    build_manifest,
    find_annotation_files,
    read_manifest,
    write_manifest,
)
from vision.data.duplicates import DuplicateReport, find_duplicates
from vision.data.splits import SplitResult, check_leakage, make_group_splits

__all__ = [
    "ANNOTATION_EXTENSIONS",
    "IMAGE_EXTENSIONS",
    "ImageRecord",
    "build_manifest",
    "find_annotation_files",
    "read_manifest",
    "write_manifest",
    "DuplicateReport",
    "find_duplicates",
    "SplitResult",
    "check_leakage",
    "make_group_splits",
]
