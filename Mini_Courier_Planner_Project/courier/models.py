"""Core data structures used by every phase of the planner.

Data design (Phase 1)
---------------------
Parcel   : pid, weight (kg, int), priority (1-5, 5 = most important),
           deadline_h (hours after dispatch), destination (graph node id)
Node     : id, name, x, y  (x, y are only used for drawing the map)
Graph    : undirected weighted graph stored as an ADJACENCY LIST
           {node: [(neighbour, distance_km), ...]}
Problem  : one complete input = graph + nodes + parcels + vehicle settings
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class Parcel:
    pid: str
    weight: int          # kg - must be an integer so it can index the DP table
    priority: int        # 1 (low) .. 5 (high)
    deadline_h: float    # delivery deadline, hours after the van leaves
    destination: int     # node id in the customer graph

    @property
    def value(self) -> int:
        """Benefit of loading this parcel (the 'profit' in the knapsack).

        value = 10 * priority + urgency bonus, where the bonus is
        (24 - deadline_h) for deadlines inside 24 h and 0 afterwards.
        So an important AND urgent parcel is the most valuable to load.
        """
        return int(self.priority * 10 + max(0.0, 24.0 - self.deadline_h))


@dataclass(frozen=True)
class Node:
    id: int
    name: str
    x: float
    y: float


class Graph:
    """Undirected weighted graph (adjacency list)."""

    def __init__(self) -> None:
        self.adj: Dict[int, List[Tuple[int, float]]] = {}

    def add_node(self, u: int) -> None:
        self.adj.setdefault(u, [])

    def add_edge(self, u: int, v: int, w: float) -> None:
        if w < 0:
            raise ValueError("Dijkstra requires non-negative edge weights")
        self.add_node(u)
        self.add_node(v)
        self.adj[u].append((v, w))
        self.adj[v].append((u, w))

    def nodes(self) -> List[int]:
        return sorted(self.adj)

    def edges(self) -> List[Tuple[int, int, float]]:
        seen = []
        for u in self.adj:
            for v, w in self.adj[u]:
                if u < v:
                    seen.append((u, v, w))
        return sorted(seen)

    def __len__(self) -> int:
        return len(self.adj)


@dataclass
class Problem:
    name: str
    graph: Graph
    nodes: Dict[int, Node]
    parcels: List[Parcel]
    depot: int = 0
    capacity: int = 25          # van capacity in kg
    speed_kmh: float = 40.0
    service_min: float = 5.0    # minutes spent at every stop
