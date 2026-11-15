"""Phase 4 - performance testing.  Run:  python run_benchmarks.py
Writes CSV tables to outputs/ , charts to outputs/charts/ and a correctness log."""
import copy
import csv
import random
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from courier import verification as V
from courier.charts import line_chart, route_map
from courier.data_io import load_problem
from courier.generator import generate_problem, random_graph, random_parcels
from courier.graph import (dijkstra, held_karp, nearest_neighbor_tour, stop_distances,
                           tour_length, two_opt)
from courier.knapsack import (knapsack_bruteforce, knapsack_dp, knapsack_greedy,
                              knapsack_value_only)
from courier.planner import plan_all_trips, plan_trip
from courier.sorting import SORTERS, parcel_key

ROOT = Path(__file__).resolve().parent
OUT, CH = ROOT / "outputs", ROOT / "outputs" / "charts"
OUT.mkdir(exist_ok=True); CH.mkdir(exist_ok=True)


def best_of(fn, repeat=3):
    """Smallest wall-clock time (s) over `repeat` runs - the usual timeit convention."""
    import gc
    times = []
    for _ in range(max(repeat, 5)):          # at least 5 runs: removes one-off noise
        gc.collect(); gc.disable()           # keep garbage collection out of the timing
        t0 = time.perf_counter(); fn(); times.append(time.perf_counter() - t0)
        gc.enable()
    return min(times)


def write_csv(name, header, rows):
    with open(OUT / name, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(header); w.writerows(rows)


# ------------------------------------------------------------------ 1. sorting
def bench_sorting():
    sizes = [100, 500, 1000, 2000, 5000, 10000]
    slow_limit = 5000
    rows, series = [], {a: ([], []) for a in SORTERS}
    for n in sizes:
        data = random_parcels(n, 50, seed=5)
        for name, fn in SORTERS.items():
            if name == "insertion" and n > slow_limit:
                continue
            t = best_of(lambda: fn(data, parcel_key), 3 if n <= 2000 else 2)
            rows.append([name, n, "random", f"{t * 1000:.4f}"])
            series[name][0].append(n); series[name][1].append(t * 1000)
    line_chart(CH / "sorting_runtime.png", "Sorting runtime vs number of parcels (random order)",
               "number of parcels n (log scale)", "time in ms (log scale)", series, True, True)

    # input pattern experiment at n = 2000
    n, pat_rows, patterns = 2000, [], {}
    base = sorted(random_parcels(n, 50, seed=6), key=parcel_key)
    patterns["random"] = random_parcels(n, 50, seed=6)
    patterns["already sorted"] = base
    patterns["reverse sorted"] = base[::-1]
    for pname, data in patterns.items():
        for name, fn in SORTERS.items():
            t = best_of(lambda: fn(data, parcel_key), 2)
            pat_rows.append([name, pname, f"{t * 1000:.4f}"])
    write_csv("sorting_runtime.csv", ["algorithm", "n", "input", "ms"], rows)
    write_csv("sorting_patterns_n2000.csv", ["algorithm", "input", "ms"], pat_rows)
    return rows, pat_rows


# --------------------------------------------------------------- 2. knapsack
def bench_knapsack():
    rng = random.Random(9)
    # (a) DP vs brute force (exponential)
    rows_a, dp_t, bf_t, ns = [], [], [], list(range(8, 21, 2))
    for n in ns:
        w = [rng.randint(1, 15) for _ in range(n)]; v = [rng.randint(1, 100) for _ in range(n)]
        cap = sum(w) // 3
        t1 = best_of(lambda: knapsack_dp(w, v, cap), 3)
        t2 = best_of(lambda: knapsack_bruteforce(w, v, cap), 1)
        dp_t.append(t1 * 1000); bf_t.append(t2 * 1000)
        rows_a.append([n, cap, f"{t1 * 1000:.4f}", f"{t2 * 1000:.4f}"])
    line_chart(CH / "knapsack_dp_vs_bruteforce.png",
               "0/1 Knapsack: Dynamic Programming vs brute force",
               "number of parcels n", "time in ms (log scale)",
               {"DP  O(nW)": (ns, dp_t), "Brute force  O(2^n)": (ns, bf_t)}, False, True)
    # (b) DP scaling in n at fixed W, and in W at fixed n
    sizes = [100, 200, 400, 800, 1600]
    rows_b, t_full, t_1d = [], [], []
    for n in sizes:
        w = [rng.randint(1, 15) for _ in range(n)]; v = [rng.randint(1, 100) for _ in range(n)]
        a = best_of(lambda: knapsack_dp(w, v, 300), 2)
        b = best_of(lambda: knapsack_value_only(w, v, 300), 2)
        t_full.append(a * 1000); t_1d.append(b * 1000)
        rows_b.append([n, 300, f"{a * 1000:.3f}", f"{b * 1000:.3f}"])
    line_chart(CH / "knapsack_scaling.png", "Knapsack DP runtime grows linearly with n (W = 300)",
               "number of parcels n", "time in ms",
               {"2-D table (with trace-back)": (sizes, t_full), "1-D row (value only)": (sizes, t_1d)})
    write_csv("knapsack_dp_vs_bruteforce.csv", ["n", "capacity", "dp_ms", "bruteforce_ms"], rows_a)
    write_csv("knapsack_scaling.csv", ["n", "capacity", "dp_2d_ms", "dp_1d_ms"], rows_b)
    return rows_a, rows_b


# ------------------------------------------------------------- 3. graph / TSP
def bench_graph():
    rows, ns, dj = [], [20, 50, 100, 200, 400, 800, 1600], []
    for n in ns:
        g, _ = random_graph(n, seed=3)
        t = best_of(lambda: dijkstra(g, 0), 5)
        dj.append(t * 1000); rows.append(["dijkstra_single_source", n, f"{t * 1000:.4f}"])
    line_chart(CH / "dijkstra_runtime.png", "Dijkstra (binary heap): one source",
               "number of nodes V", "time in ms", {"Dijkstra": (ns, dj)})

    g, _ = random_graph(400, seed=4)
    ks, t_ap, t_nn, t_2o = [5, 10, 20, 40, 80, 160], [], [], []
    for k in ks:
        stops = list(range(0, k + 1))
        ap = best_of(lambda: stop_distances(g, stops), 2)
        dist, _p = stop_distances(g, stops)
        nn = best_of(lambda: nearest_neighbor_tour(dist, 0, stops), 3)
        tour = nearest_neighbor_tour(dist, 0, stops)
        o2 = best_of(lambda: two_opt(tour, dist), 2)
        t_ap.append(ap * 1000); t_nn.append(nn * 1000); t_2o.append(o2 * 1000)
        rows += [["dijkstra_from_all_stops", k, f"{ap * 1000:.4f}"],
                 ["nearest_neighbour", k, f"{nn * 1000:.4f}"], ["two_opt", k, f"{o2 * 1000:.4f}"]]
    line_chart(CH / "route_steps_runtime.png", "Route construction vs number of stops k (V = 400)",
               "number of stops k (log scale)", "time in ms (log scale)",
               {"Dijkstra from every stop": (ks, t_ap), "Nearest neighbour": (ks, t_nn),
                "2-opt improvement": (ks, t_2o)}, True, True)
    write_csv("graph_runtime.csv", ["step", "size", "ms"], rows)

    # approximation quality vs exact Held-Karp
    rng = random.Random(12)
    qual, ks_q, nn_r, opt_r = [], [5, 6, 7, 8, 9, 10, 11], [], []
    for k in ks_q:
        r1, r2 = [], []
        for t in range(25):
            g2, _ = random_graph(30, seed=100 * k + t)
            stops = [0] + rng.sample(range(1, 30), k)
            dist, _p = stop_distances(g2, stops)
            nn_t = nearest_neighbor_tour(dist, 0, stops)
            opt, _o = held_karp(dist, 0, stops)
            r1.append(tour_length(nn_t, dist) / opt)
            r2.append(tour_length(two_opt(nn_t, dist), dist) / opt)
        nn_r.append(statistics.mean(r1)); opt_r.append(statistics.mean(r2))
        qual.append([k, f"{statistics.mean(r1):.4f}", f"{max(r1):.4f}",
                     f"{statistics.mean(r2):.4f}", f"{max(r2):.4f}"])
    line_chart(CH / "tsp_quality.png", "Tour length relative to the exact optimum (25 random instances per k)",
               "number of delivery stops k", "average length / optimal length",
               {"Nearest neighbour": (ks_q, nn_r), "Nearest neighbour + 2-opt": (ks_q, opt_r),
                "Optimal (Held-Karp) = 1.0": (ks_q, [1.0] * len(ks_q))})
    write_csv("tsp_quality.csv", ["k_stops", "nn_avg_ratio", "nn_max_ratio", "2opt_avg_ratio", "2opt_max_ratio"], qual)
    return rows, qual


# ----------------------------------------------------------------- 4. pipeline
def bench_pipeline():
    import matplotlib.pyplot as plt
    cases = [("small", ROOT / "data" / "small.json"), ("medium", ROOT / "data" / "medium.json"),
             ("large", ROOT / "data" / "large.json")]
    steps = ["sort", "knapsack", "dijkstra", "tsp_nn", "two_opt"]
    rows, table = [], {}
    for label, path in cases:
        prob = load_problem(path)
        runs = []
        for _ in range(5):
            tr = plan_trip(prob, prob.parcels, "merge", use_two_opt=True)
            runs.append(tr.timings)
        med = {s: statistics.median(r[s] for r in runs) * 1000 for s in steps}
        table[label] = med
        t_all0 = time.perf_counter()
        trips, bad = plan_all_trips(prob)
        t_all = (time.perf_counter() - t_all0) * 1000
        rows.append([label, len(prob.graph), len(prob.parcels), prob.capacity, len(tr.loaded),
                     len(tr.stops), f"{tr.route_km:.1f}"] + [f"{med[s]:.4f}" for s in steps]
                    + [f"{sum(med.values()):.4f}", len(trips), f"{t_all:.2f}"])
    write_csv("pipeline_runtime.csv",
              ["dataset", "nodes", "parcels", "capacity_kg", "parcels_loaded", "stops", "route_km"]
              + [f"{s}_ms" for s in steps] + ["trip_total_ms", "trips_for_all_parcels", "all_trips_ms"], rows)

    fig, ax = plt.subplots(figsize=(8, 4.8))
    width = 0.25
    cols = ["#1f4e79", "#c0504d", "#2e8b57"]
    for i, (label, med) in enumerate(table.items()):
        xs = [j + (i - 1) * width for j in range(len(steps))]
        bars = ax.bar(xs, [med[s] for s in steps], width, label=label, color=cols[i])
        for x, s in zip(xs, steps):
            ax.text(x, med[s] * 1.1, f"{med[s]:.3g}", ha="center", fontsize=6.5, rotation=90)
    ax.set_yscale("log"); ax.set_xticks(range(len(steps)))
    ax.set_xticklabels(["Merge sort", "Knapsack DP", "Dijkstra\n(all stops)", "Nearest\nneighbour", "2-opt"])
    ax.set_ylabel("median time in ms (log scale)")
    ax.set_title("Runtime of each major step - one trip", fontsize=11, fontweight="bold")
    ax.legend(title="dataset"); ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout(); fig.savefig(CH / "pipeline_steps.png", dpi=160); plt.close(fig)

    # share of total time (stacked)
    fig, ax = plt.subplots(figsize=(8, 3.6))
    left = [0.0] * len(table)
    scol = ["#1f4e79", "#c0504d", "#2e8b57", "#e08e0b", "#7b4fa3"]
    for s, c, nice in zip(steps, scol, ["sort", "knapsack", "dijkstra", "nearest neighbour", "2-opt"]):
        vals = [100 * table[k][s] / sum(table[k].values()) for k in table]
        ax.barh(list(table), vals, left=left, color=c, label=nice)
        left = [a + b for a, b in zip(left, vals)]
    ax.set_xlabel("share of total trip-planning time (%)")
    ax.set_title("Where does the time go?", fontsize=11, fontweight="bold")
    ax.legend(fontsize=8, ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.25))
    fig.tight_layout(); fig.savefig(CH / "pipeline_share.png", dpi=160); plt.close(fig)

    # route maps
    for label, path in cases[:2]:
        prob = load_problem(path)
        trip = plan_trip(prob, prob.parcels, "merge", use_two_opt=(label != "small"))
        route_map(prob, trip, CH / f"route_{label}.png")
    return rows


# --------------------------------------------------------- 5. correctness log
def correctness():
    lines = ["CORRECTNESS EVIDENCE (randomised tests)", "=" * 60]
    n, res = V.check_sorting(200)
    for name, ok in res.items():
        lines.append(f"Sorting  {name:<10}: {ok}/{n} random lists identical to reference order")
    n, ok, gw = V.check_knapsack(200)
    lines.append(f"Knapsack DP == brute force == 1-D DP, weight <= capacity : {ok}/{n} instances")
    lines.append(f"  (greedy by ratio was strictly worse than DP on {gw}/{n} of them)")
    n, ok = V.check_dijkstra(40)
    lines.append(f"Dijkstra == Floyd-Warshall for every source node         : {ok}/{n} random graphs")
    n, valid, bounded, improved, avg, mx = V.check_tsp(40)
    lines.append(f"Nearest-neighbour tour is a valid closed tour            : {valid}/{n}")
    lines.append(f"NN length >= exact optimum (Held-Karp)                   : {bounded}/{n}")
    lines.append(f"2-opt never makes the tour longer                        : {improved}/{n}")
    lines.append(f"NN / optimal length: average {avg:.3f}, worst {mx:.3f}")
    text = "\n".join(lines)
    (OUT / "logs" / "correctness_report.txt").write_text(text + "\n")
    return text


if __name__ == "__main__":
    print("Sorting ...");   bench_sorting()
    print("Knapsack ...");  bench_knapsack()
    print("Graph ...");     bench_graph()
    print("Pipeline ...");  bench_pipeline()
    print(correctness())
    print("\nAll CSV files and charts written to", OUT)
