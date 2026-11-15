"""Phase 2a - Parcel prioritisation (sorting).

Order required by the courier:  earliest deadline first; if two parcels have
the same deadline the higher priority goes first; the parcel id is the final
tie-breaker so the order is fully deterministic.

Chosen algorithm: MERGE SORT
  * O(n log n) in the best, average AND worst case (no bad inputs),
  * stable, and
  * simple to trace by hand in a viva.
Quick sort, heap sort and insertion sort are implemented as well so that
Phase 4 can compare them experimentally. Every sorter first "decorates" the
items with their key (computed once) and then compares keys only.
"""
from __future__ import annotations

import random
from typing import Callable, List, Sequence

from .models import Parcel


def parcel_key(p: Parcel):
    """Sort key: (deadline asc, priority desc, id asc)."""
    return (p.deadline_h, -p.priority, p.pid)


def _decorate(items, key):
    return [(key(x), x) for x in items]


def _undecorate(pairs):
    return [x for _, x in pairs]


# ---------------------------------------------------------------- merge sort
def _merge_sort(a):
    if len(a) <= 1:
        return a
    mid = len(a) // 2
    left, right = _merge_sort(a[:mid]), _merge_sort(a[mid:])
    out, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if right[j][0] < left[i][0]:       # strict '<' keeps equal keys in order (stable)
            out.append(right[j]); j += 1
        else:
            out.append(left[i]); i += 1
    out.extend(left[i:])
    out.extend(right[j:])
    return out


def merge_sort(items: Sequence, key: Callable = parcel_key) -> List:
    return _undecorate(_merge_sort(_decorate(items, key)))


# ---------------------------------------------------------------- quick sort
def quick_sort(items: Sequence, key: Callable = parcel_key, seed: int = 7) -> List:
    a = _decorate(items, key)
    rng = random.Random(seed)

    def partition(lo, hi):
        r = rng.randint(lo, hi)            # random pivot avoids the O(n^2) worst case
        a[r], a[hi] = a[hi], a[r]
        pivot = a[hi][0]
        i = lo
        for j in range(lo, hi):
            if a[j][0] < pivot:
                a[i], a[j] = a[j], a[i]
                i += 1
        a[i], a[hi] = a[hi], a[i]
        return i

    def qs(lo, hi):
        while lo < hi:                      # recurse on the smaller side -> O(log n) stack
            p = partition(lo, hi)
            if p - lo < hi - p:
                qs(lo, p - 1); lo = p + 1
            else:
                qs(p + 1, hi); hi = p - 1

    qs(0, len(a) - 1)
    return _undecorate(a)


# ----------------------------------------------------------------- heap sort
def heap_sort(items: Sequence, key: Callable = parcel_key) -> List:
    a = _decorate(items, key)
    n = len(a)

    def sift_down(i, size):
        while True:
            l, r, big = 2 * i + 1, 2 * i + 2, i
            if l < size and a[big][0] < a[l][0]:
                big = l
            if r < size and a[big][0] < a[r][0]:
                big = r
            if big == i:
                return
            a[i], a[big] = a[big], a[i]
            i = big

    for i in range(n // 2 - 1, -1, -1):     # build max-heap, O(n)
        sift_down(i, n)
    for end in range(n - 1, 0, -1):         # extract max n-1 times, O(n log n)
        a[0], a[end] = a[end], a[0]
        sift_down(0, end)
    return _undecorate(a)


# ------------------------------------------------------------ insertion sort
def insertion_sort(items: Sequence, key: Callable = parcel_key) -> List:
    a = _decorate(items, key)
    for i in range(1, len(a)):
        cur, j = a[i], i - 1
        while j >= 0 and cur[0] < a[j][0]:
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = cur
    return _undecorate(a)


def builtin_sort(items: Sequence, key: Callable = parcel_key) -> List:
    """Python's Timsort - used only as a reference / baseline."""
    return sorted(items, key=key)


SORTERS = {
    "merge": merge_sort,
    "quick": quick_sort,
    "heap": heap_sort,
    "insertion": insertion_sort,
    "timsort": builtin_sort,
}


def prioritise(parcels: Sequence[Parcel], algorithm: str = "merge") -> List[Parcel]:
    """Return parcels in dispatch-priority order using the chosen algorithm."""
    return SORTERS[algorithm](parcels, parcel_key)
