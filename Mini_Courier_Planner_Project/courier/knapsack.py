"""Phase 2b - Box filling with 0/1 Knapsack (dynamic programming).

Each parcel is either loaded (1) or left for a later trip (0); it cannot be
split.  Weight = parcel kg, value = Parcel.value (priority + urgency),
capacity = van capacity in kg.

    T[i][w] = best value using the first i parcels with capacity w
    T[i][w] = T[i-1][w]                                   if wt[i] > w
            = max(T[i-1][w], T[i-1][w-wt[i]] + val[i])    otherwise

Time  O(n*W)   Space O(n*W)  (O(W) if only the value is needed)
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import List, Optional, Sequence


@dataclass
class KnapsackResult:
    best_value: int
    chosen: List[int]                 # indices (into the input order) of loaded parcels
    total_weight: int
    table: Optional[List[List[int]]] = None


def knapsack_dp(weights: Sequence[int], values: Sequence[int], capacity: int,
                keep_table: bool = True) -> KnapsackResult:
    n = len(weights)
    T = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        wt, val = weights[i - 1], values[i - 1]
        prev, cur = T[i - 1], T[i]
        for w in range(capacity + 1):
            cur[w] = prev[w]
            if wt <= w and prev[w - wt] + val > cur[w]:
                cur[w] = prev[w - wt] + val

    # Trace back: if the value changed between row i-1 and row i, parcel i was loaded.
    chosen, w = [], capacity
    for i in range(n, 0, -1):
        if T[i][w] != T[i - 1][w]:
            chosen.append(i - 1)
            w -= weights[i - 1]
    chosen.reverse()
    return KnapsackResult(T[n][capacity], chosen,
                          sum(weights[i] for i in chosen),
                          T if keep_table else None)


def knapsack_value_only(weights: Sequence[int], values: Sequence[int], capacity: int) -> int:
    """Space-optimised version: one row, iterate capacity backwards. O(W) memory."""
    row = [0] * (capacity + 1)
    for wt, val in zip(weights, values):
        for w in range(capacity, wt - 1, -1):
            cand = row[w - wt] + val
            if cand > row[w]:
                row[w] = cand
    return row[capacity]


def knapsack_greedy(weights: Sequence[int], values: Sequence[int], capacity: int) -> KnapsackResult:
    """Greedy by value/weight ratio - fast but NOT always optimal (comparison only)."""
    order = sorted(range(len(weights)), key=lambda i: values[i] / weights[i], reverse=True)
    chosen, used, total = [], 0, 0
    for i in order:
        if used + weights[i] <= capacity:
            chosen.append(i); used += weights[i]; total += values[i]
    return KnapsackResult(total, sorted(chosen), used)


def knapsack_bruteforce(weights: Sequence[int], values: Sequence[int], capacity: int) -> int:
    """Try all 2^n subsets - only for verification / the runtime comparison."""
    best, n = 0, len(weights)
    for r in range(n + 1):
        for combo in combinations(range(n), r):
            if sum(weights[i] for i in combo) <= capacity:
                best = max(best, sum(values[i] for i in combo))
    return best
