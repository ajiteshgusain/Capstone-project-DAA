"""Reading and writing datasets (JSON) plus CSV exports for easy viewing."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from .models import Graph, Node, Parcel, Problem


def load_problem(path) -> Problem:
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    g = Graph()
    nodes = {}
    for n in raw["nodes"]:
        nodes[n["id"]] = Node(n["id"], n["name"], n["x"], n["y"])
        g.add_node(n["id"])
    for u, v, w in raw["edges"]:
        g.add_edge(u, v, w)
    parcels = [Parcel(p["id"], int(p["weight"]), int(p["priority"]),
                      float(p["deadline_h"]), int(p["destination"]))
               for p in raw["parcels"]]
    for p in parcels:
        if p.destination not in nodes:
            raise ValueError(f"Parcel {p.pid} has unknown destination {p.destination}")
        if p.weight <= 0:
            raise ValueError(f"Parcel {p.pid} must have a positive integer weight")
    return Problem(
        name=raw.get("name", Path(path).stem), graph=g, nodes=nodes, parcels=parcels,
        depot=raw.get("depot", 0), capacity=int(raw["vehicle_capacity_kg"]),
        speed_kmh=float(raw.get("speed_kmh", 40)),
        service_min=float(raw.get("service_min", 5)),
    )


def save_problem(problem: Problem, path) -> None:
    raw = {
        "name": problem.name,
        "depot": problem.depot,
        "vehicle_capacity_kg": problem.capacity,
        "speed_kmh": problem.speed_kmh,
        "service_min": problem.service_min,
        "nodes": [{"id": n.id, "name": n.name, "x": n.x, "y": n.y}
                  for n in problem.nodes.values()],
        "edges": [[u, v, w] for u, v, w in problem.graph.edges()],
        "parcels": [{"id": p.pid, "weight": p.weight, "priority": p.priority,
                     "deadline_h": p.deadline_h, "destination": p.destination}
                    for p in problem.parcels],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(raw, fh, indent=2)


def export_parcels_csv(problem: Problem, path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["parcel_id", "weight_kg", "priority", "deadline_h", "destination", "value"])
        for p in problem.parcels:
            wr.writerow([p.pid, p.weight, p.priority, p.deadline_h, p.destination, p.value])


def export_edges_csv(problem: Problem, path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["from", "to", "distance_km"])
        for u, v, w in problem.graph.edges():
            wr.writerow([u, v, w])
