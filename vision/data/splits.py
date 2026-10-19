"""Leakage-safe, deterministic train/validation/test splits.

Policy (applied in this order, every exclusion recorded with a reason):

1. Unreadable images are excluded (`unreadable`).
2. Images without a usable class (folder not mapped to a class) are excluded (`unmapped_label`).
3. A duplicate group whose members carry different labels is excluded as a whole
   (`label_conflict`) until a person resolves it. No label is silently picked.
4. Within a duplicate group only one representative is kept; redundant exact or near copies
   are excluded (`duplicate_of:<sample_id>`) so they cannot inflate weight or metrics.
5. Representatives sharing a capture-metadata key supplied by the caller (site, session,
   sequence) form one unit. Units are assigned whole, never split, so related photographs
   cannot straddle train and test. A unit may contain several classes.
6. Assignment is stratified by each unit's majority class: units are shuffled with a seeded
   RNG and allocated greedily to the split furthest below its target share of samples.

The same manifest, class mapping, ratios and seed always produce the same assignment.
"""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from vision.data.manifest import ImageRecord

SPLITS = ("train", "val", "test")


@dataclass
class SplitResult:
    seed: int
    ratios: Dict[str, float]
    assignments: Dict[str, str]  # sample_id -> split, kept samples only
    exclusions: Dict[str, str]  # sample_id -> reason
    class_counts: Dict[str, Dict[str, int]] = field(default_factory=dict)
    group_counts: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "seed": self.seed,
            "ratios": self.ratios,
            "kept": len(self.assignments),
            "excluded": len(self.exclusions),
            "exclusion_reasons": dict(Counter(r.split(":")[0] for r in self.exclusions.values())),
            "class_counts": self.class_counts,
            "group_counts": self.group_counts,
        }


def _validate_ratios(ratios: Mapping[str, float]) -> Dict[str, float]:
    if set(ratios) != set(SPLITS):
        raise ValueError(f"ratios must have exactly the keys {SPLITS}")
    if any(v < 0 for v in ratios.values()) or abs(sum(ratios.values()) - 1.0) > 1e-6:
        raise ValueError("ratios must be non-negative and sum to 1")
    return {k: float(ratios[k]) for k in SPLITS}


def make_group_splits(
    records: Sequence[ImageRecord],
    class_of_folder: Union[Mapping[str, str], Callable[[ImageRecord], Optional[str]]],
    ratios: Optional[Mapping[str, float]] = None,
    seed: int = 1337,
    extra_groups: Optional[Mapping[str, str]] = None,
    keep_duplicates_in: Iterable[str] = (),
) -> SplitResult:
    """Assign kept samples to train/val/test.

    Args:
        records: manifest records, already annotated by `find_duplicates` (duplicate_group set).
        class_of_folder: maps folder_label -> class name, or a callable record -> class name
            (e.g. "crack"/"background" from box labels). Records with no class are excluded.
        ratios: target share of *samples* per split; default 0.70/0.15/0.15.
        seed: RNG seed for the group shuffle.
        extra_groups: optional sample_id -> grouping key from capture metadata (site, session,
            sequence). Samples sharing a key are kept in the same split, in addition to
            duplicate grouping.
        keep_duplicates_in: splits in which every member of a duplicate group is kept rather
            than one representative (e.g. ("train",) when the copies are photometric
            augmentations with their own labels). Evaluation splits should never be listed.
    """
    if callable(class_of_folder):
        class_of = class_of_folder
    else:
        mapping = class_of_folder
        class_of = lambda rec: mapping.get(rec.folder_label)  # noqa: E731
    keep_all = set(keep_duplicates_in)
    bad = keep_all - set(SPLITS)
    if bad:
        raise ValueError(f"keep_duplicates_in has unknown splits {sorted(bad)}")
    r = _validate_ratios(ratios or {"train": 0.70, "val": 0.15, "test": 0.15})
    exclusions: Dict[str, str] = {}

    usable: List[ImageRecord] = []
    for rec in records:
        if not rec.readable:
            exclusions[rec.sample_id] = "unreadable"
        elif class_of(rec) is None:
            exclusions[rec.sample_id] = "unmapped_label"
        elif rec.duplicate_group is None:
            raise ValueError("records must be annotated by find_duplicates before splitting")
        else:
            usable.append(rec)

    # 1) Duplicate groups: one class and one representative each. A duplicate group whose
    #    copies carry different labels is a label conflict and is excluded for review.
    dup_members: Dict[str, List[ImageRecord]] = defaultdict(list)
    for rec in usable:
        dup_members[rec.duplicate_group].append(rec)  # type: ignore[index]
    reps: List[ImageRecord] = []
    copies: Dict[str, List[ImageRecord]] = {}
    for gid in sorted(dup_members):
        recs = sorted(dup_members[gid], key=lambda x: x.rel_path)
        if len({class_of(x) for x in recs}) > 1:
            for x in recs:
                exclusions[x.sample_id] = "label_conflict"
            continue
        rep, *redundant = recs
        reps.append(rep)
        copies[rep.sample_id] = redundant

    # 2) Capture-metadata grouping (site, session, sequence): representatives sharing a key
    #    form one unit that goes to a single split. A unit may legitimately mix classes.
    unit_of: Dict[str, str] = {rep.sample_id: rep.duplicate_group for rep in reps}  # type: ignore[misc]
    if extra_groups:
        parent: Dict[str, str] = {}

        def find(g: str) -> str:
            while parent.get(g, g) != g:
                g = parent[g]
            return g

        by_key: Dict[str, List[str]] = defaultdict(list)
        for rep in reps:
            for sid in [m.sample_id for m in dup_members[rep.duplicate_group]]:  # type: ignore[index]
                key = extra_groups.get(sid)
                if key is not None:
                    by_key[key].append(rep.sample_id)
        for ids in by_key.values():
            roots = sorted({find(unit_of[i]) for i in ids})
            for other in roots[1:]:
                parent[other] = roots[0]
        unit_of = {sid: find(u) for sid, u in unit_of.items()}

    units: Dict[str, List[ImageRecord]] = defaultdict(list)
    for rep in reps:
        units[unit_of[rep.sample_id]].append(rep)

    # 3) Stratify units by their majority class, then fill each split towards its target
    #    share of samples, largest units first within a seeded order.
    units_by_class: Dict[str, List[Tuple[str, List[ImageRecord]]]] = defaultdict(list)
    for uid in sorted(units):
        counts = Counter(class_of(x) for x in units[uid])
        majority = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        units_by_class[majority].append((uid, sorted(units[uid], key=lambda x: x.rel_path)))

    rng = random.Random(seed)
    assignments: Dict[str, str] = {}
    class_counts: Dict[str, Dict[str, int]] = {s: {} for s in SPLITS}
    group_counts: Dict[str, int] = {s: 0 for s in SPLITS}

    for cls in sorted(units_by_class):
        items = units_by_class[cls]
        rng.shuffle(items)
        items.sort(key=lambda it: -len(it[1]))  # stable: big units placed first, seeded order within a size
        n = sum(len(recs) for _, recs in items)
        target = {s: r[s] * n for s in SPLITS}
        got = {s: 0 for s in SPLITS}
        for _, recs in items:
            # Split furthest below its target (ties broken in SPLITS order).
            split = max(SPLITS, key=lambda s: (target[s] - got[s], -SPLITS.index(s)))
            got[split] += len(recs)
            group_counts[split] += 1
            for x in recs:
                assignments[x.sample_id] = split
                c = class_of(x)
                class_counts[split][c] = class_counts[split].get(c, 0) + 1  # type: ignore[index]
                for dup_copy in copies[x.sample_id]:
                    if split in keep_all:
                        assignments[dup_copy.sample_id] = split
                        class_counts[split][c] = class_counts[split].get(c, 0) + 1  # type: ignore[index]
                    else:
                        exclusions[dup_copy.sample_id] = f"duplicate_of:{x.sample_id}"

    for rec in records:
        rec.split = assignments.get(rec.sample_id)
        rec.exclusion_reason = exclusions.get(rec.sample_id)

    return SplitResult(
        seed=seed,
        ratios=r,
        assignments=assignments,
        exclusions=exclusions,
        class_counts=class_counts,
        group_counts=group_counts,
    )


def check_leakage(records: Sequence[ImageRecord]) -> List[str]:
    """Return human-readable violations; an empty list means no group spans two splits
    and no exact content (SHA-256) appears in two splits."""
    problems: List[str] = []
    split_of_group: Dict[str, set] = defaultdict(set)
    split_of_hash: Dict[str, set] = defaultdict(set)
    for rec in records:
        if rec.split is None:
            continue
        if rec.duplicate_group:
            split_of_group[rec.duplicate_group].add(rec.split)
        split_of_hash[rec.sha256].add(rec.split)
    for gid, splits in sorted(split_of_group.items()):
        if len(splits) > 1:
            problems.append(f"duplicate group {gid} appears in {sorted(splits)}")
    for h, splits in sorted(split_of_hash.items()):
        if len(splits) > 1:
            problems.append(f"identical content {h[:12]} appears in {sorted(splits)}")
    return problems
