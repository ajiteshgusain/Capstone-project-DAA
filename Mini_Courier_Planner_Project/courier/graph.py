"""Phase 3 - Route maker: Dijkstra + nearest-neighbour TSP approximation.

Step 1  Dijkstra from the depot and from every delivery stop gives the true
        road distance between any two stops (the graph is sparse, so the
        direct "distance" between two customers is usually a multi-hop path).
Step 2  Those distances form a complete "stop graph".  Visiting every stop
        once and returning to the depot is the Travelling Salesman Problem
        (NP-hard), so we use the NEAREST-NEIGHBOUR heuristic: always drive to
        the closest unvisited stop.   O(k^2) for k stops.
Step 3  (Optimisation, Phase 4) 2-opt removes crossing legs from that tour.
        Held-Karp (exact, O(k^2 * 2^k)) is only used on tiny inputs to
        measure how far the heuristic is from optimal.
"""
from __future__ import annotations

import heapq
import math
from typing import Dict, List, Optional, Sequence, Tuple

from .models import Graph

INF = math.inf


# ------------------------------------------------------------------ Dijkstra
def dijkstra(graph: Graph, source: int) -> Tuple[Dict[int, float], Dict[int, Optional[int]]]:
    """Single-source shortest paths with a binary heap. O((V + E) log V)."""
    dist = {u: INF for u in graph.adj}
    prev: Dict[int, Optional[int]] = {u: None for u in graph.adj}
    dist[source] = 0.0
    heap = [(0.0, source)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:                      # stale entry (lazy deletion)
            continue
        for v, w in graph.adj[u]:
            nd = d + w
            if nd < dist[v]:                 # relax edge (u, v)
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))
    return dist, prev


def reconstruct_path(prev: Dict[int, Optional[int]], source: int, target: int) -> List[int]:
    path, cur = [], target
    while cur is not None:
        path.append(cur)
        if cur == source:
            return path[::-1]
        cur = prev[cur]
    raise ValueError(f"No path from {source} to {target}")


def stop_distances(graph: Graph, terminals: Sequence[int]):
    """Run Dijkstra from every terminal. Returns (dist[u][v], prev[u])."""
    dist: Dict[int, Dict[int, float]] = {}
    prevs: Dict[int, Dict[int, Optional[int]]] = {}
    for u in terminals:
        d, p = dijkstra(graph, u)
        for v in terminals:
            if d[v] == INF:
                raise ValueError(f"Node {v} is unreachable from {u}: graph is disconnected")
        dist[u] = {v: d[v] for v in terminals}
        prevs[u] = p
    return dist, prevs


# ------------------------------------------------------- TSP approximations
def tour_length(tour: Sequence[int], dist) -> float:
    return sum(dist[tour[i]][tour[i + 1]] for i in range(len(tour) - 1))


def nearest_neighbor_tour(dist, start: int, stops: Sequence[int]) -> List[int]:
    """Greedy tour start -> ... -> start. Ties go to the smaller node id."""
    unvisited = set(stops) - {start}
    tour, cur = [start], start
    while unvisited:
        nxt = min(unvisited, key=lambda s: (dist[cur][s], s))
        tour.append(nxt)
        unvisited.remove(nxt)
        cur = nxt
    tour.append(start)
    return tour


def two_opt(tour: Sequence[int], dist) -> List[int]:
    """Local search: reverse a segment whenever that shortens the tour."""
    best = list(tour)
    improved = True
    while improved:
        improved = False
        for i in range(1, len(best) - 2):
            for j in range(i + 1, len(best) - 1):
                a, b = best[i - 1], best[i]
                c, d = best[j], best[j + 1]
                if dist[a][c] + dist[b][d] < dist[a][b] + dist[c][d] - 1e-9:
                    best[i:j + 1] = reversed(best[i:j + 1])
                    improved = True
    return best


def held_karp(dist, start: int, stops: Sequence[int]) -> Tuple[float, List[int]]:
    """Exact TSP by DP over subsets - only for <= ~12 stops (benchmark baseline)."""
    s = [x for x in stops if x != start]
    k = len(s)
    if k == 0:
        return 0.0, [start, start]
    full = 1 << k
    dp = [[INF] * k for _ in range(full)]
    parent = [[-1] * k for _ in range(full)]
    for j in range(k):
        dp[1 << j][j] = dist[start][s[j]]
    for mask in range(full):
        for j in range(k):
            if not mask & (1 << j) or dp[mask][j] == INF:
                continue
            for t in range(k):
                if mask & (1 << t):
                    continue
                nm = mask | (1 << t)
                cand = dp[mask][j] + dist[s[j]][s[t]]
                if cand < dp[nm][t]:
                    dp[nm][t] = cand
                    parent[nm][t] = j
    last = min(range(k), key=lambda j: dp[full - 1][j] + dist[s[j]][start])
    best = dp[full - 1][last] + dist[s[last]][start]
    order, mask, j = [], full - 1, last
    while j != -1:
        order.append(s[j])
        pj = parent[mask][j]
        mask ^= 1 << j
        j = pj
    return best, [start] + order[::-1] + [start]


def expand_route(tour: Sequence[int], prevs) -> List[int]:
    """Replace every leg of the stop-tour by its real road path."""
    full = [tour[0]]
    for a, b in zip(tour, tour[1:]):
        leg = reconstruct_path(prevs[a], a, b)
        full.extend(leg[1:])
    return full


# ------------------------------------------------- reference (for testing)
def floyd_warshall(graph: Graph):
    nodes = graph.nodes()
    d = {u: {v: (0.0 if u == v else INF) for v in nodes} for u in nodes}
    for u in nodes:
        for v, w in graph.adj[u]:
            d[u][v] = min(d[u][v], w)
    for k in nodes:
        for i in nodes:
            for j in nodes:
                if d[i][k] + d[k][j] < d[i][j]:
                    d[i][j] = d[i][k] + d[k][j]
    return d
