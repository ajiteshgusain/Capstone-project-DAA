"""Creates the three sample datasets in ./data (run once; results are committed).

small  : hand-made, 8 customers-nodes / 10 parcels -> can be traced by hand in a viva
medium : generated, 30 nodes / 100 parcels
large  : generated, 120 nodes / 1000 parcels
"""
from pathlib import Path

from courier.data_io import export_edges_csv, export_parcels_csv, save_problem
from courier.generator import generate_problem
from courier.models import Graph, Node, Parcel, Problem

DATA = Path(__file__).parent / "data"


def small_problem() -> Problem:
    names = {0: "Depot (Sector 18)", 1: "Sector 14", 2: "DLF Phase 3", 3: "Cyber Hub",
             4: "Sohna Road", 5: "Golf Course Rd", 6: "MG Road", 7: "Udyog Vihar"}
    xy = {0: (0, 4), 1: (3, 7), 2: (4, 3), 3: (7, 6), 4: (6, 0), 5: (10, 3), 6: (10, 0), 7: (13, 5)}
    edges = [(0, 1, 4), (0, 2, 6), (1, 2, 3), (1, 3, 7), (2, 3, 4), (2, 4, 8), (3, 5, 5),
             (4, 5, 6), (4, 6, 5), (5, 6, 3), (5, 7, 9), (6, 7, 4), (3, 7, 10)]
    g = Graph()
    for u in names:
        g.add_node(u)
    for u, v, w in edges:
        g.add_edge(u, v, float(w))
    nodes = {u: Node(u, names[u], *xy[u]) for u in names}
    #           id    kg pri dl  dest
    rows = [("P01", 5, 5, 2, 1), ("P02", 8, 3, 6, 2), ("P03", 4, 4, 3, 3),
            ("P04", 7, 2, 8, 4), ("P05", 3, 5, 2, 5), ("P06", 6, 3, 5, 6),
            ("P07", 9, 1, 10, 7), ("P08", 2, 4, 4, 1), ("P09", 5, 2, 9, 3),
            ("P10", 6, 4, 3, 6)]
    parcels = [Parcel(a, b, c, float(d), e) for a, b, c, d, e in rows]
    return Problem("small_sample", g, nodes, parcels, depot=0, capacity=25)


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    datasets = [small_problem(),
                generate_problem("medium_sample", 30, 100, 100, seed=11),
                generate_problem("large_sample", 120, 1000, 300, seed=21)]
    for prob in datasets:
        stem = prob.name.replace("_sample", "")
        save_problem(prob, DATA / f"{stem}.json")
        export_parcels_csv(prob, DATA / f"{stem}_parcels.csv")
        export_edges_csv(prob, DATA / f"{stem}_edges.csv")
        print(f"{stem:7s}: {len(prob.graph)} nodes, {len(prob.graph.edges())} edges, "
              f"{len(prob.parcels)} parcels, capacity {prob.capacity} kg")
