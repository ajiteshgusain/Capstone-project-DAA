"""Captures the real console output of the main commands and renders each as a PNG
('screenshot') in outputs/screenshots, plus the raw text in outputs/logs."""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from courier.charts import terminal_image

SS, LOGS = ROOT / "outputs" / "screenshots", ROOT / "outputs" / "logs"
SS.mkdir(parents=True, exist_ok=True); LOGS.mkdir(parents=True, exist_ok=True)


def run(args):
    r = subprocess.run([sys.executable] + args, cwd=ROOT, capture_output=True, text=True)
    return r.stdout + r.stderr


def split_sections(text):
    """Split console output at the '=====' banner lines into (title, body) blocks."""
    parts = re.split(r"\n=+\n([^\n]+)\n=+\n", "\n" + text)
    secs = {}
    for i in range(1, len(parts), 2):
        secs[parts[i]] = parts[i + 1]
    return secs


def banner(title, body):
    return f"{'=' * 78}\n{title}\n{'=' * 78}\n{body.rstrip()}"


# 1. small sample, full trace
small = run(["main.py"])
(LOGS / "run_small.txt").write_text(small)
sec = split_sections(small)
keys = list(sec)
get = lambda prefix: next(k for k in keys if k.startswith(prefix))
terminal_image(f"$ python main.py\n" + banner(get("MINI"), sec[get("MINI")]) + "\n" +
               banner(get("PHASE 2a"), sec[get("PHASE 2a")]),
               SS / "01_phase2_sorting.png", "Phase 2a - sorted parcels")
terminal_image("$ python main.py   (continued)\n" + banner(get("PHASE 2b"), sec[get("PHASE 2b")]),
               SS / "02_phase2_knapsack_dp_table.png", "Phase 2b - DP table and packing plan")
terminal_image("$ python main.py   (continued)\n" + banner(get("PHASE 3a"), sec[get("PHASE 3a")]) + "\n" +
               banner(get("PHASE 3b"), sec[get("PHASE 3b")]),
               SS / "03_phase3_dijkstra_route.png", "Phase 3 - Dijkstra and nearest-neighbour route")

# 2. medium dataset, all trips + 2-opt
med = run(["main.py", "--dataset", "data/medium.json", "--all-trips", "--two-opt", "--no-table"])
(LOGS / "run_medium_all_trips.txt").write_text(med)
lines = med.strip("\n").split("\n")
terminal_image("$ python main.py --dataset data/medium.json --all-trips --two-opt\n" + "\n".join(lines[:lines.index("Details of trip 1:") + 1]),
               SS / "04_medium_all_trips.png", "Medium dataset - all trips")

# 3. large dataset (summary part only)
large = run(["main.py", "--dataset", "data/large.json", "--all-trips", "--two-opt", "--no-table"])
(LOGS / "run_large_all_trips.txt").write_text(large)
ll = large.strip("\n").split("\n")
terminal_image("$ python main.py --dataset data/large.json --all-trips --two-opt\n" + "\n".join(ll[:ll.index("Details of trip 1:") + 1]),
               SS / "05_large_all_trips.png", "Large dataset - 1000 parcels")

# 4. unit tests
tests = run(["-m", "unittest", "discover", "-s", "tests", "-v"])
(LOGS / "unit_tests.txt").write_text(tests)
terminal_image("$ python -m unittest discover -s tests -v\n" + tests, SS / "06_unit_tests.png", "Unit tests")

# 5. correctness report + pipeline runtime table
corr = (LOGS / "correctness_report.txt").read_text()
pipe = (ROOT / "outputs" / "pipeline_runtime.csv").read_text().replace(",", " | ")
terminal_image("$ python run_benchmarks.py   (correctness + pipeline summary)\n" + corr + "\n" +
               "PIPELINE RUNTIME (ms)\n" + pipe.replace("\r", ""),
               SS / "07_correctness_and_runtime.png", "Benchmark summary", width=130)
print("screenshots written:", sorted(p.name for p in SS.glob("*.png")))
