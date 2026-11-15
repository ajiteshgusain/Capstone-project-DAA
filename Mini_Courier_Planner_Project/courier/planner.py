"""Integration layer: sorting -> knapsack -> Dijkstra -> TSP route.

plan_trip()      builds ONE delivery trip and times every major step.
plan_all_trips() repeats it until every deliverable parcel has been planned.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List

from .graph import (expand_route, nearest_neighbor_tour, stop_distances,
                    tour_length, two_opt)
from .knapsack import KnapsackResult, knapsack_dp
from .models import Parcel, Problem
from .sorting import prioritise


@dataclass
class Delivery:
    node: int
    arrival_h: float
    parcels: List[Parcel]
    on_time: bool


@dataclass
class TripPlan:
    sorted_parcels: List[Parcel]
    knapsack: KnapsackResult
    loaded: List[Parcel]
    left_over: List[Parcel]
    stops: List[int]
    tour: List[int]                 # stop order incl. depot at both ends
    route: List[int]                # full road path (every graph node passed)
    route_km: float
    deliveries: List[Delivery]
    return_h: float
    timings: Dict[str, float] = field(default_factory=dict)


def _time(timings, name, fn, *a, **k):
    t0 = time.perf_counter()
    out = fn(*a, **k)
    timings[name] = time.perf_counter() - t0
    return out


def plan_trip(problem: Problem, parcels: List[Parcel], sorter: str = "merge",
              use_two_opt: bool = False, keep_table: bool = True) -> TripPlan:
    timings: Dict[str, float] = {}

    # Phase 2a: prioritise
    ordered = _time(timings, "sort", prioritise, parcels, sorter)

    # Phase 2b: choose the parcels for this trip (0/1 knapsack)
    ks = _time(timings, "knapsack", knapsack_dp,
               [p.weight for p in ordered], [p.value for p in ordered],
               problem.capacity, keep_table)
    loaded = [ordered[i] for i in ks.chosen]
    chosen_idx = set(ks.chosen)
    left_over = [p for i, p in enumerate(ordered) if i not in chosen_idx]

    # Phase 3a: shortest paths between depot and every stop
    stops = sorted({p.destination for p in loaded})
    terminals = [problem.depot] + [s for s in stops if s != problem.depot]
    dist, prevs = _time(timings, "dijkstra", stop_distances, problem.graph, terminals)

    # Phase 3b: nearest-neighbour tour (+ optional 2-opt)
    tour = _time(timings, "tsp_nn", nearest_neighbor_tour, dist, problem.depot, terminals)
    if use_two_opt:
        tour = _time(timings, "two_opt", two_opt, tour, dist)
    route = expand_route(tour, prevs)
    km = tour_length(tour, dist)

    # Deadline check: drive time + service time at each stop
    clock, deliveries = 0.0, []
    by_stop: Dict[int, List[Parcel]] = {}
    for p in loaded:
        by_stop.setdefault(p.destination, []).append(p)
    for a, b in zip(tour, tour[1:]):
        clock += dist[a][b] / problem.speed_kmh
        if b == problem.depot:
            break
        deliveries.append(Delivery(b, clock, by_stop[b],
                                   all(clock <= p.deadline_h for p in by_stop[b])))
        clock += problem.service_min / 60.0
    return_h = sum(dist[a][b] for a, b in zip(tour, tour[1:])) / problem.speed_kmh \
        + len(deliveries) * problem.service_min / 60.0
    return TripPlan(ordered, ks, loaded, left_over, stops, tour, route, km,
                    deliveries, return_h, timings)


def plan_all_trips(problem: Problem, sorter: str = "merge", use_two_opt: bool = False):
    """Keep dispatching vans until nothing deliverable is left.
    Returns (trips, undeliverable_parcels)."""
    remaining = [p for p in problem.parcels if p.weight <= problem.capacity]
    undeliverable = [p for p in problem.parcels if p.weight > problem.capacity]
    trips = []
    while remaining:
        trip = plan_trip(problem, remaining, sorter, use_two_opt, keep_table=False)
        if not trip.loaded:               # safety net - cannot happen with weight <= capacity
            undeliverable.extend(remaining)
            break
        trips.append(trip)
        loaded_ids = {p.pid for p in trip.loaded}
        remaining = [p for p in remaining if p.pid not in loaded_ids]
    return trips, undeliverable
