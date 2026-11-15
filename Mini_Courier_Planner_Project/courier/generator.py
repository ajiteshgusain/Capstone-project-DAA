"""Synthetic dataset generator (reproducible: every dataset uses a fixed seed)."""
from __future__ import annotations

import math
import random

from .models import Graph, Node, Parcel, Problem


def random_graph(n_nodes: int, seed: int = 1, area: float = 100.0, k_near: int = 3):
    """Connected random road network: every node linked to its k nearest
    neighbours, then extra links join any separate components."""
    rng = random.Random(seed)
    pts = {0: (area / 2, area / 2)}                       # depot in the middle
    for i in range(1, n_nodes):
        pts[i] = (round(rng.uniform(0, area), 1), round(rng.uniform(0, area), 1))
    names = {0: "Depot"}
    names.update({i: f"C{i:03d}" for i in range(1, n_nodes)})

    def d(a, b):
        return math.dist(pts[a], pts[b])

    edges = {}
    for u in pts:
        near = sorted((v for v in pts if v != u), key=lambda v: d(u, v))[:k_near]
        for v in near:
            edges[(min(u, v), max(u, v))] = round(d(u, v) * rng.uniform(1.0, 1.3), 1)

    # make sure the network is connected (union-find over current edges)
    parent = {u: u for u in pts}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for (u, v) in edges:
        parent[find(u)] = find(v)
    comps = {}
    for u in pts:
        comps.setdefault(find(u), []).append(u)
    roots = list(comps)
    while len(roots) > 1:
        a_nodes, b_nodes = comps[roots[0]], comps[roots[1]]
        u, v = min(((a, b) for a in a_nodes for b in b_nodes), key=lambda p: d(*p))
        edges[(min(u, v), max(u, v))] = round(d(u, v) * 1.1, 1)
        comps[roots[0]] = a_nodes + b_nodes
        del comps[roots[1]]
        roots = list(comps)

    g = Graph()
    for u in pts:
        g.add_node(u)
    for (u, v), w in sorted(edges.items()):
        g.add_edge(u, v, w)
    nodes = {u: Node(u, names[u], *pts[u]) for u in pts}
    return g, nodes


def random_parcels(n_parcels: int, n_nodes: int, seed: int = 1, max_weight: int = 15):
    rng = random.Random(seed + 1000)
    return [Parcel(f"P{i:04d}", rng.randint(1, max_weight), rng.randint(1, 5),
                   float(rng.randint(1, 24)), rng.randint(1, n_nodes - 1))
            for i in range(1, n_parcels + 1)]


def generate_problem(name: str, n_nodes: int, n_parcels: int, capacity: int,
                     seed: int = 1) -> Problem:
    g, nodes = random_graph(n_nodes, seed)
    return Problem(name, g, nodes, random_parcels(n_parcels, n_nodes, seed),
                   depot=0, capacity=capacity)
