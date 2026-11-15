"""Collects real measured numbers into outputs/report_data.json (consumed by the report builder)."""
import csv, json
from pathlib import Path
from PIL import Image
from courier.data_io import load_problem
from courier.planner import plan_trip
from courier.graph import dijkstra, reconstruct_path

R = Path(__file__).resolve().parent
O = R / "outputs"
rd = lambda n: list(csv.DictReader(open(O / n, newline="")))

prob = load_problem(R / "data" / "small.json")
trip = plan_trip(prob, prob.parcels)
dist, prev = dijkstra(prob.graph, 0)
data = {
  "sorted": [[i + 1, p.pid, p.weight, p.priority, p.deadline_h, p.destination, p.value]
             for i, p in enumerate(trip.sorted_parcels)],
  "loaded": [p.pid for p in trip.loaded], "left": [p.pid for p in trip.left_over],
  "best_value": trip.knapsack.best_value, "weight": trip.knapsack.total_weight,
  "tour": trip.tour, "route": trip.route, "km": trip.route_km, "hours": trip.return_h,
  "dijkstra": [[s, prob.nodes[s].name, dist[s], " -> ".join(map(str, reconstruct_path(prev, 0, s)))]
               for s in trip.stops],
  "deliveries": [[d.node, prob.nodes[d.node].name, round(d.arrival_h, 2),
                  min(p.deadline_h for p in d.parcels), "On time" if d.on_time else "Late",
                  ", ".join(p.pid for p in d.parcels)] for d in trip.deliveries],
  "sorting": rd("sorting_runtime.csv"), "patterns": rd("sorting_patterns_n2000.csv"),
  "kn_bf": rd("knapsack_dp_vs_bruteforce.csv"), "kn_sc": rd("knapsack_scaling.csv"),
  "graph": rd("graph_runtime.csv"), "tsp": rd("tsp_quality.csv"), "pipe": rd("pipeline_runtime.csv"),
  "correct": (O / "logs" / "correctness_report.txt").read_text().splitlines(),
  "img": {},
}
for p in list((O / "charts").glob("*.png")) + list((O / "screenshots").glob("*.png")):
    w, h = Image.open(p).size
    data["img"][p.stem] = [str(p), w, h]
json.dump(data, open(O / "report_data.json", "w"), indent=1)
print("ok", len(data["img"]), "images")
