"""Mini-Courier Planner - command line demo.

Examples
--------
python main.py                                   # small sample, full trace
python main.py --dataset data/medium.json        # bigger input
python main.py --dataset data/medium.json --all-trips --two-opt
python main.py --sorter quick --no-table
python main.py --plot outputs/charts/route_small.png
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from courier.data_io import load_problem
from courier.graph import dijkstra, held_karp, reconstruct_path, tour_length
from courier.planner import plan_all_trips, plan_trip
from courier.sorting import SORTERS

LINE = "=" * 78


def head(title):
    print(f"\n{LINE}\n{title}\n{LINE}")


def show_parcels(rows, title):
    print(title)
    print(f"{'#':>3} {'ID':<6}{'kg':>4}{'prio':>6}{'deadline(h)':>13}{'dest':>6}{'value':>7}")
    for i, p in enumerate(rows, 1):
        print(f"{i:>3} {p.pid:<6}{p.weight:>4}{p.priority:>6}{p.deadline_h:>13.1f}"
              f"{p.destination:>6}{p.value:>7}")


def show_dp_table(trip, capacity):
    T = trip.knapsack.table
    n = len(trip.sorted_parcels)
    print("DP table T[i][w] (rows = parcels considered in priority order, columns = capacity kg)")
    print("      " + "".join(f"{w:>4}" for w in range(capacity + 1)))
    for i in range(n + 1):
        label = "none" if i == 0 else trip.sorted_parcels[i - 1].pid
        print(f"{label:<6}" + "".join(f"{v:>4}" for v in T[i]))


def show_trip(problem, trip, trace_table=True, optimal_check=True):
    nm = lambda u: problem.nodes[u].name
    head("PHASE 2a - PARCELS SORTED BY (deadline asc, priority desc)")
    show_parcels(trip.sorted_parcels[:25], "")
    if len(trip.sorted_parcels) > 25:
        print(f"... {len(trip.sorted_parcels) - 25} more parcels not shown")

    head(f"PHASE 2b - 0/1 KNAPSACK (capacity {problem.capacity} kg)")
    if trace_table and trip.knapsack.table and problem.capacity <= 30 and len(trip.sorted_parcels) <= 15:
        show_dp_table(trip, problem.capacity)
        print()
    print(f"Best total value : {trip.knapsack.best_value}")
    print(f"Weight loaded    : {trip.knapsack.total_weight} / {problem.capacity} kg")
    show_parcels(trip.loaded, "Loaded parcels:")
    left = ", ".join(p.pid for p in trip.left_over[:30])
    print(f"Left for next trip ({len(trip.left_over)}): {left}{' ...' if len(trip.left_over) > 30 else ''}")

    head("PHASE 3a - DIJKSTRA SHORTEST DISTANCES FROM THE DEPOT")
    dist, prev = dijkstra(problem.graph, problem.depot)
    for s in trip.stops[:15]:
        path = " -> ".join(str(x) for x in reconstruct_path(prev, problem.depot, s))
        print(f"  depot -> {s:>3} ({nm(s):<16}) {dist[s]:>7.1f} km   path: {path}")
    if len(trip.stops) > 15:
        print(f"  ... {len(trip.stops) - 15} more stops")

    head("PHASE 3b - NEAREST-NEIGHBOUR DELIVERY ROUTE")
    print("Stop order :", " -> ".join(str(x) for x in trip.tour))
    print("Named      :", " -> ".join(nm(x) for x in trip.tour[:12]) + (" ..." if len(trip.tour) > 12 else ""))
    print("Road route :", " -> ".join(str(x) for x in trip.route[:40]) + (" ..." if len(trip.route) > 40 else ""))
    print(f"Route length: {trip.route_km:.1f} km   |  driving+service time: {trip.return_h:.2f} h")
    if optimal_check and len(trip.stops) <= 11:
        from courier.graph import stop_distances
        terminals = [problem.depot] + [s for s in trip.stops if s != problem.depot]
        d2, _ = stop_distances(problem.graph, terminals)
        opt, otour = held_karp(d2, problem.depot, terminals)
        print(f"Exact optimum (Held-Karp): {opt:.1f} km  -> heuristic is "
              f"{100 * (trip.route_km / opt - 1):.1f}% above optimal" if opt else "")
    print("\nDelivery schedule:")
    for d in trip.deliveries[:20]:
        ids = ",".join(p.pid for p in d.parcels)
        tight = min(p.deadline_h for p in d.parcels)
        print(f"  node {d.node:>3} {nm(d.node):<16} arrive {d.arrival_h:>5.2f} h  "
              f"earliest deadline {tight:>4.1f} h  {'ON TIME' if d.on_time else 'LATE   '}  [{ids}]")
    late = sum(not d.on_time for d in trip.deliveries)
    print(f"On-time stops: {len(trip.deliveries) - late}/{len(trip.deliveries)}")

    head("TIMING OF MAJOR STEPS (milliseconds)")
    for k, v in trip.timings.items():
        print(f"  {k:<10} {v * 1000:>9.3f} ms")
    print(f"  {'total':<10} {sum(trip.timings.values()) * 1000:>9.3f} ms")


def main():
    ap = argparse.ArgumentParser(description="Mini-Courier Planner")
    ap.add_argument("--dataset", default=str(Path(__file__).parent / "data" / "small.json"))
    ap.add_argument("--sorter", choices=sorted(SORTERS), default="merge")
    ap.add_argument("--two-opt", action="store_true", help="improve the tour with 2-opt")
    ap.add_argument("--all-trips", action="store_true", help="plan every trip until all parcels are delivered")
    ap.add_argument("--no-table", action="store_true", help="do not print the DP table")
    ap.add_argument("--plot", metavar="PNG", help="save a route map image")
    a = ap.parse_args()

    problem = load_problem(a.dataset)
    head(f"MINI-COURIER PLANNER | dataset: {problem.name}")
    print(f"Nodes: {len(problem.graph)}   Roads: {len(problem.graph.edges())}   "
          f"Parcels: {len(problem.parcels)}   Van capacity: {problem.capacity} kg   "
          f"Sorter: {a.sorter}   2-opt: {a.two_opt}")

    if a.all_trips:
        trips, bad = plan_all_trips(problem, a.sorter, a.two_opt)
        head("ALL-TRIPS PLAN")
        print(f"{'trip':>4} {'parcels':>8} {'kg':>5} {'value':>7} {'stops':>6} {'km':>8} {'hours':>7}")
        for i, t in enumerate(trips, 1):
            print(f"{i:>4} {len(t.loaded):>8} {t.knapsack.total_weight:>5} {t.knapsack.best_value:>7}"
                  f" {len(t.stops):>6} {t.route_km:>8.1f} {t.return_h:>7.2f}")
        print(f"Total: {sum(len(t.loaded) for t in trips)} parcels in {len(trips)} trips, "
              f"{sum(t.route_km for t in trips):.1f} km; undeliverable: {len(bad)}")
        trip = trips[0]
        print("\nDetails of trip 1:")
    else:
        trip = plan_trip(problem, problem.parcels, a.sorter, a.two_opt)
    show_trip(problem, trip, trace_table=not a.no_table)

    if a.plot:
        from courier.charts import route_map
        route_map(problem, trip, a.plot)
        print(f"\nRoute map saved to {a.plot}")


if __name__ == "__main__":
    main()
