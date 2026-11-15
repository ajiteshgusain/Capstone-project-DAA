"""Randomised correctness checks shared by the unit tests and the benchmark report."""
from __future__ import annotations

import math
import random

from .generator import random_graph
from .graph import (dijkstra, floyd_warshall, held_karp, nearest_neighbor_tour,
                    stop_distances, tour_length, two_opt)
from .knapsack import knapsack_bruteforce, knapsack_dp, knapsack_greedy, knapsack_value_only
from .models import Parcel
from .sorting import SORTERS, parcel_key


def _rand_parcels(rng, n):
    return [Parcel(f"P{i:03d}", rng.randint(1, 9), rng.randint(1, 5),
                   float(rng.randint(1, 12)), 1) for i in range(n)]


def check_sorting(trials=200, seed=1):
    rng = random.Random(seed)
    results = {name: 0 for name in SORTERS}
    for _ in range(trials):
        ps = _rand_parcels(rng, rng.randint(0, 60))
        expected = sorted(ps, key=parcel_key)
        for name, fn in SORTERS.items():
            if fn(ps) == expected:
                results[name] += 1
    return trials, results


def check_knapsack(trials=200, seed=2):
    rng = random.Random(seed)
    ok = greedy_worse = 0
    for _ in range(trials):
        n = rng.randint(1, 12)
        wts = [rng.randint(1, 12) for _ in range(n)]
        vals = [rng.randint(1, 60) for _ in range(n)]
        cap = rng.randint(5, 40)
        r = knapsack_dp(wts, vals, cap)
        brute = knapsack_bruteforce(wts, vals, cap)
        good = (r.best_value == brute == knapsack_value_only(wts, vals, cap)
                and r.total_weight <= cap and sum(vals[i] for i in r.chosen) == r.best_value)
        ok += good
        greedy_worse += knapsack_greedy(wts, vals, cap).best_value < brute
    return trials, ok, greedy_worse


def check_dijkstra(trials=40, seed=3):
    ok = 0
    for t in range(trials):
        n = random.Random(seed + t).randint(5, 40)
        g, _ = random_graph(n, seed=seed + t)
        fw = floyd_warshall(g)
        good = True
        for src in g.nodes():
            d, _p = dijkstra(g, src)
            good &= all(math.isclose(d[v], fw[src][v], abs_tol=1e-6) for v in g.nodes())
        ok += good
    return trials, ok


def check_tsp(trials=40, seed=4):
    """NN tour must be a valid cycle; NN >= optimal; 2-opt <= NN."""
    rng = random.Random(seed)
    valid = bounded = improved = 0
    ratios = []
    for t in range(trials):
        n = 12
        g, _ = random_graph(n, seed=seed + t)
        stops = list(range(0, rng.randint(4, 9) + 1))
        dist, _ = stop_distances(g, stops)
        nn = nearest_neighbor_tour(dist, 0, stops)
        valid += (nn[0] == nn[-1] == 0 and sorted(nn[:-1]) == sorted(stops))
        opt, _t = held_karp(dist, 0, stops)
        L = tour_length(nn, dist)
        bounded += (L >= opt - 1e-9)
        improved += (tour_length(two_opt(nn, dist), dist) <= L + 1e-9)
        ratios.append(L / opt if opt else 1.0)
    return trials, valid, bounded, improved, sum(ratios) / len(ratios), max(ratios)
