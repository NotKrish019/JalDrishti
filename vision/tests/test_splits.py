"""Leakage-safe splitting."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from vision.data.duplicates import find_duplicates
from vision.data.manifest import build_manifest
from vision.data.splits import check_leakage, make_group_splits

FOLDERS = {"Damaged_images": "visible_deterioration_folder", "Background_images": "background_folder_unconfirmed"}


def _split(root: Path, seed: int = 1337, extra=None):
    records = list(build_manifest(root))
    find_duplicates(records)
    result = make_group_splits(records, FOLDERS, seed=seed, extra_groups=extra)
    return records, result


def test_no_duplicate_group_or_content_crosses_splits(synthetic_dataset: Path) -> None:
    records, _ = _split(synthetic_dataset)
    assert check_leakage(records) == []


def test_exclusions_are_recorded_with_reasons(synthetic_dataset: Path) -> None:
    records, result = _split(synthetic_dataset)
    reasons = Counter(r.split(":")[0] for r in result.exclusions.values())
    assert reasons["unreadable"] == 2
    assert reasons["label_conflict"] == 2  # both members of the cross-folder duplicate
    assert reasons["duplicate_of"] >= 2  # exact copy and re-encoded copy
    by_name = {r.rel_path.split("/")[-1]: r for r in records}
    assert by_name["mislabelled_bg3.jpg"].split is None
    assert by_name["ND (3).jpg"].exclusion_reason == "label_conflict"
    # every record is either assigned or excluded, never both
    for r in records:
        assert (r.split is None) != (r.exclusion_reason is None)


def test_split_is_deterministic_and_seed_sensitive(synthetic_dataset: Path) -> None:
    _, a = _split(synthetic_dataset, seed=1)
    _, b = _split(synthetic_dataset, seed=1)
    _, c = _split(synthetic_dataset, seed=2)
    assert a.assignments == b.assignments
    assert a.assignments != c.assignments


def test_split_is_stratified(synthetic_dataset: Path) -> None:
    _, result = _split(synthetic_dataset)
    for split in ("train", "val", "test"):
        assert set(result.class_counts[split]) == set(FOLDERS.values()), f"{split} is missing a class"
    train = sum(result.class_counts["train"].values())
    assert train >= 0.6 * len(result.assignments)


def test_metadata_groups_stay_together(synthetic_dataset: Path) -> None:
    records = list(build_manifest(synthetic_dataset))
    session = {r.sample_id: "session_A" for r in records if r.rel_path.endswith(("(4).jpg", "(5).jpg", "(6).jpg"))}
    find_duplicates(records)
    make_group_splits(records, FOLDERS, extra_groups=session)
    splits = {r.split for r in records if r.sample_id in session and r.split}
    assert len(splits) == 1


def test_leakage_detector_catches_violations(synthetic_dataset: Path) -> None:
    records, _ = _split(synthetic_dataset)
    kept = [r for r in records if r.split]
    kept[0].duplicate_group, kept[1].duplicate_group = "g_shared", "g_shared"
    kept[0].split, kept[1].split = "train", "test"
    assert any("g_shared" in p for p in check_leakage(records))


def test_requires_duplicate_annotation(synthetic_dataset: Path) -> None:
    with pytest.raises(ValueError):
        make_group_splits(list(build_manifest(synthetic_dataset)), FOLDERS)


def test_rejects_bad_ratios(synthetic_dataset: Path) -> None:
    records = list(build_manifest(synthetic_dataset))
    find_duplicates(records)
    with pytest.raises(ValueError):
        make_group_splits(records, FOLDERS, ratios={"train": 0.9, "val": 0.2, "test": 0.0})


def test_duplicates_can_be_kept_in_train_only(synthetic_dataset: Path) -> None:
    seen_train_group = False
    for seed in range(8):
        records = list(build_manifest(synthetic_dataset))
        report = find_duplicates(records)
        make_group_splits(records, FOLDERS, seed=seed, keep_duplicates_in=("train",))
        assert check_leakage(records) == []
        for gid, ids in report.groups.items():
            if gid in report.label_conflicts:
                continue
            splits = [r.split for r in records if r.sample_id in ids]
            assigned = [x for x in splits if x]
            if "train" in assigned:
                seen_train_group = True
                assert assigned == ["train"] * len(ids), "all copies kept, all in train"
            else:
                assert len(assigned) == 1, "val/test keep exactly one representative"
    assert seen_train_group
    with pytest.raises(ValueError):
        make_group_splits(records, FOLDERS, keep_duplicates_in=("holdout",))


def test_callable_class_mapping(synthetic_dataset: Path) -> None:
    records = list(build_manifest(synthetic_dataset))
    find_duplicates(records)
    result = make_group_splits(records, lambda r: "a" if r.rel_path.endswith("(1).jpg") else ("b" if r.readable else None))
    assert check_leakage(records) == []
    assert set().union(*(set(c) for c in result.class_counts.values())) <= {"a", "b"}
