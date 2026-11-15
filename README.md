# Mini-Courier Planner (DAA Capstone - ETCCDA302)

An integrated Python prototype that turns a list of parcels and a road network into
**an ordered delivery route and an optimised packing plan**.

| Stage | Algorithm | Complexity |
|---|---|---|
| Prioritise parcels (deadline asc, priority desc) | Merge sort | O(n log n) |
| Choose parcels for one van trip | 0/1 Knapsack - Dynamic Programming | O(n·W) |
| Shortest road distance between stops | Dijkstra (binary heap) | O((V+E) log V) per source |
| Order of the stops | Nearest-neighbour TSP (+ optional 2-opt) | O(k²) |

Quick, heap and insertion sort, greedy knapsack, brute force and Held-Karp are included
only for the Phase 4 comparisons.

## Requirements
Python 3.9+. The algorithms use only the standard library. `matplotlib` and `Pillow`
are needed only for charts / screenshots: `pip install -r requirements.txt`

## Run
```bash
python main.py                                    # small sample, full trace with DP table
python main.py --dataset data/medium.json --all-trips --two-opt
python main.py --dataset data/large.json  --all-trips --two-opt --no-table
python main.py --sorter quick --plot outputs/charts/route.png   # choose sorter, save route map
python run_benchmarks.py                          # Phase 4: runtimes, CSV tables, charts (~1 min)
python make_screenshots.py                        # console-output screenshots
python -m unittest discover -s tests -v           # 16 unit tests
python generate_data.py                           # recreate data/*.json and CSV files
```
Use your own data: copy `data/small.json`, edit parcels / edges, run with `--dataset your.json`.

## Layout
```
main.py  run_benchmarks.py  make_screenshots.py  generate_data.py
courier/   models.py data_io.py sorting.py knapsack.py graph.py planner.py
           generator.py verification.py charts.py
tests/     test_all.py
data/      small | medium | large  (.json + _parcels.csv + _edges.csv)
outputs/   charts/ (runtime charts, route maps, design diagram)
           screenshots/ (console output captures)   logs/ (raw text of every run)
           *.csv (measured runtimes)
Mini_Courier_Planner_Report.docx / .pdf   full report
```

## Key results (this machine)
* Small sample: 6 parcels loaded (value 361, 25/25 kg), route 0→1→3→5→6→0 = 37.0 km (equal to the exact optimum), all deadlines met.
* 1,000 parcels / 120 nodes: one trip planned in ~24 ms, all 27 trips in ~0.23 s.
* DP = brute force on 200/200 random instances; Dijkstra = Floyd-Warshall on 40/40 graphs;
  nearest neighbour averages ~5 % above optimal, 2-opt < 0.5 %.
