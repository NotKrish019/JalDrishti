"""Exact and near-duplicate detection.

Three distinct ideas, kept separate in the report:

* Exact duplicate   identical file bytes (same SHA-256).
* Near duplicate    64-bit difference hashes within `max_distance` bits (Hamming), i.e. the
                    same picture re-encoded, rescaled or very lightly edited.
* Related image     a different photograph of the same wall or scene. Hashing cannot find
                    these; they need capture metadata (site, session, sequence). Splits group
                    by whatever metadata exists; with none, this leakage risk is documented.

Candidate near-duplicate pairs are found with banded hashing: the 64-bit hash is split into
8 bands of 8 bits. Two hashes within 7 bits of each other must agree exactly on at least one
band (pigeonhole), so with max_distance <= 7 no qualifying pair is missed.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

from vision.data.manifest import ImageRecord

DEFAULT_NEAR_DISTANCE = 6
_BANDS = 8


def hamming(a: str, b: str) -> int:
    return bin(int(a, 16) ^ int(b, 16)).count("1")


class _UnionFind:
    def __init__(self, items: Sequence[str]) -> None:
        self.parent = {i: i for i in items}

    def find(self, x: str) -> str:
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            # Deterministic: the lexicographically smaller id becomes the root.
            lo, hi = sorted((ra, rb))
            self.parent[hi] = lo


@dataclass
class DuplicateReport:
    method: Dict[str, object]
    exact_groups: List[List[str]] = field(default_factory=list)
    near_pairs: List[Tuple[str, str, int]] = field(default_factory=list)
    # Connected components over exact + near links; singletons omitted.
    groups: Dict[str, List[str]] = field(default_factory=dict)
    # Groups whose members carry more than one folder label: need human review.
    label_conflicts: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def exact_duplicate_files(self) -> int:
        """Files beyond the first in each exact group (i.e. redundant copies)."""
        return sum(len(g) - 1 for g in self.exact_groups)

    def to_dict(self) -> Dict:
        return {
            "method": self.method,
            "exact_group_count": len(self.exact_groups),
            "exact_duplicate_files": self.exact_duplicate_files,
            "exact_groups": self.exact_groups,
            "near_pair_count": len(self.near_pairs),
            "near_pairs": [{"a": a, "b": b, "hamming": d} for a, b, d in self.near_pairs],
            "group_count": len(self.groups),
            "groups": self.groups,
            "label_conflict_count": len(self.label_conflicts),
            "label_conflicts": self.label_conflicts,
        }


def find_duplicates(records: Sequence[ImageRecord], max_distance: int = DEFAULT_NEAR_DISTANCE) -> DuplicateReport:
    """Annotate each record's `duplicate_group` and return the full report.

    Every readable record gets a group id; records with no duplicates form a group of one,
    which is what the splitter consumes.
    """
    if not 0 <= max_distance < _BANDS:
        raise ValueError(f"max_distance must be in [0, {_BANDS - 1}] for banded search to be exhaustive")

    usable = [r for r in records if r.readable]
    by_id = {r.sample_id: r for r in usable}
    uf = _UnionFind(sorted(by_id))

    exact: Dict[str, List[str]] = defaultdict(list)
    for r in usable:
        exact[r.sha256].append(r.sample_id)
    exact_groups = [sorted(ids) for ids in exact.values() if len(ids) > 1]
    for ids in exact_groups:
        for other in ids[1:]:
            uf.union(ids[0], other)

    buckets: Dict[Tuple[int, str], List[str]] = defaultdict(list)
    for r in usable:
        if not r.dhash:
            continue
        for b in range(_BANDS):
            buckets[(b, r.dhash[b * 2 : b * 2 + 2])].append(r.sample_id)

    seen = set()
    near_pairs: List[Tuple[str, str, int]] = []
    for ids in buckets.values():
        if len(ids) < 2:
            continue
        ids = sorted(ids)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = ids[i], ids[j]
                if (a, b) in seen:
                    continue
                seen.add((a, b))
                if by_id[a].sha256 == by_id[b].sha256:
                    continue  # already an exact duplicate
                d = hamming(by_id[a].dhash, by_id[b].dhash)  # type: ignore[arg-type]
                if d <= max_distance:
                    near_pairs.append((a, b, d))
                    uf.union(a, b)
    near_pairs.sort()

    members: Dict[str, List[str]] = defaultdict(list)
    for sid in sorted(by_id):
        members[uf.find(sid)].append(sid)
    groups: Dict[str, List[str]] = {}
    label_conflicts: Dict[str, List[str]] = {}
    for root, ids in members.items():
        gid = "g_" + root[2:]
        for sid in ids:
            by_id[sid].duplicate_group = gid
        if len(ids) > 1:
            groups[gid] = ids
            labels = sorted({str(by_id[s].folder_label) for s in ids})
            if len(labels) > 1:
                label_conflicts[gid] = labels

    return DuplicateReport(
        method={
            "exact": "SHA-256 of file bytes",
            "near": f"64-bit dHash (9x8 grayscale, Lanczos), Hamming distance <= {max_distance}",
            "candidate_search": f"{_BANDS} bands of 8 bits; exhaustive for distance <= {_BANDS - 1}",
            "related_images": "not detectable by hashing; requires capture metadata",
        },
        exact_groups=sorted(exact_groups),
        near_pairs=near_pairs,
        groups=groups,
        label_conflicts=label_conflicts,
    )
