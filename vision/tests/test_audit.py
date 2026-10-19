"""Dataset audit: manifest, validation, duplicates, annotation inventory.

Owner: Krish (Computer Vision / AI)
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts.vision.audit_dataset import audit_dataset, calculate_file_hash, find_dataset_dir
from vision.data.duplicates import find_duplicates, hamming
from vision.data.manifest import build_manifest, find_annotation_files, read_manifest, write_manifest


def test_manifest_records_relative_paths_and_validation(synthetic_dataset: Path) -> None:
    records = list(build_manifest(synthetic_dataset))
    paths = [r.rel_path for r in records]
    assert len(set(paths)) == len(paths)
    assert all(not p.startswith("/") and "\\" not in p for p in paths)
    assert all(str(synthetic_dataset) not in p for p in paths)
    by_name = {r.rel_path.split("/")[-1]: r for r in records}

    assert by_name["0 (0).jpg"].readable and by_name["0 (0).jpg"].width == 96
    assert by_name["0 (0).jpg"].folder_label == "Damaged_images"
    assert by_name["broken.jpg"].readable is False and "unreadable" in by_name["broken.jpg"].flags
    assert by_name["empty.jpg"].readable is False and "empty_file" in by_name["empty.jpg"].flags
    assert by_name["ND (gray).jpg"].mode == "L" and "mode_L" in by_name["ND (gray).jpg"].flags


def test_manifest_is_deterministic(synthetic_dataset: Path, tmp_path: Path) -> None:
    a = write_manifest(build_manifest(synthetic_dataset), tmp_path / "a.jsonl")
    b = write_manifest(build_manifest(synthetic_dataset), tmp_path / "b.jsonl")
    assert a == b
    assert (tmp_path / "a.jsonl").read_bytes() == (tmp_path / "b.jsonl").read_bytes()
    assert [r.sample_id for r in read_manifest(tmp_path / "a.jsonl")] == [
        r.sample_id for r in build_manifest(synthetic_dataset)
    ]


def test_exact_near_and_cross_label_duplicates(synthetic_dataset: Path) -> None:
    records = list(build_manifest(synthetic_dataset))
    report = find_duplicates(records, max_distance=6)
    by_name = {r.rel_path.split("/")[-1]: r for r in records}

    exact_members = {sid for g in report.exact_groups for sid in g}
    assert by_name["0 (0).jpg"].sample_id in exact_members
    assert by_name["copy_of_0.jpg"].sample_id in exact_members

    near = {(a, b) for a, b, _ in report.near_pairs}
    pair = tuple(sorted((by_name["0 (1).jpg"].sample_id, by_name["reencoded_1.jpg"].sample_id)))
    assert pair in near
    assert by_name["0 (1).jpg"].duplicate_group == by_name["reencoded_1.jpg"].duplicate_group

    # The same image found in both folders is flagged for review, not silently resolved.
    g = by_name["mislabelled_bg3.jpg"].duplicate_group
    assert g == by_name["ND (3).jpg"].duplicate_group
    assert g in report.label_conflicts
    assert report.label_conflicts[g] == ["Background_images", "Damaged_images"]
    # Unreadable files are never grouped.
    assert by_name["broken.jpg"].duplicate_group is None


def test_hamming() -> None:
    assert hamming("0000000000000000", "0000000000000000") == 0
    assert hamming("0000000000000000", "ffffffffffffffff") == 64
    assert hamming("000000000000000f", "0000000000000000") == 4


def test_find_duplicates_rejects_unsearchable_distance(synthetic_dataset: Path) -> None:
    with pytest.raises(ValueError):
        find_duplicates(list(build_manifest(synthetic_dataset)), max_distance=12)


def test_annotation_inventory(tmp_path: Path) -> None:
    (tmp_path / "images").mkdir()
    (tmp_path / "labels").mkdir()
    (tmp_path / "masks").mkdir()
    (tmp_path / "labels" / "a.txt").write_text("0 0.5 0.5 0.1 0.1\n")
    (tmp_path / "coco.json").write_text("{}")
    (tmp_path / "masks" / "a.png").write_bytes(b"x")
    found = find_annotation_files(tmp_path)
    assert found["yolo_txt"] == ["labels/a.txt"]
    assert found["json"] == ["coco.json"]
    assert found["mask_image"] == ["masks/a.png"]


def test_audit_summary_and_supervision(synthetic_dataset: Path) -> None:
    result = audit_dataset(synthetic_dataset)
    s = result["summary"]
    assert s["total_images"] == 34
    assert s["unreadable_images"] == 2
    assert s["images_per_folder"] == {"Background_images": 16, "Damaged_images": 18}
    assert s["exact_duplicate_redundant_files"] >= 2
    assert s["cross_label_duplicate_groups"] == 1
    assert s["annotation_files"] == {}
    assert s["supervision"]["object_detection"].startswith("not supported")
    assert s["supervision"]["segmentation"].startswith("not supported")


def test_calculate_file_hash_is_sha256(tmp_path: Path) -> None:
    f = tmp_path / "x.bin"
    f.write_bytes(b"jaldrishti")
    assert calculate_file_hash(f) == hashlib.sha256(b"jaldrishti").hexdigest()


def test_find_dataset_dir_explicit_path(tmp_path: Path, synthetic_dataset: Path) -> None:
    assert find_dataset_dir(str(synthetic_dataset)) == synthetic_dataset
    assert find_dataset_dir(str(tmp_path / "missing")) is None


@pytest.mark.skipif(find_dataset_dir() is None, reason="Darbhanga Fort dataset is not present on this machine")
def test_real_dataset_labels_are_valid() -> None:
    """Runs only where the real dataset has been extracted (data/raw/, gitignored)."""
    from vision.data.yolo_labels import check_split, summarise

    root = find_dataset_dir()
    assert root is not None
    splits = [check_split(root, s) for s in ("train", "val") if (root / s).is_dir()]
    summary = summarise(splits)
    for name, s in summary.items():
        assert s["status"].get("invalid", 0) == 0, f"{name}: invalid label files {s['invalid_examples'][:3]}"
        assert not s["orphan_labels"], f"{name}: labels without images"
        assert s["classes"] == ["crack"]
