"""Draws the Phase 1 system-design (data-flow) diagram -> outputs/charts/design_flow.png"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(figsize=(10, 4.6)); ax.set_xlim(0, 86); ax.set_ylim(0, 46); ax.axis("off")
def box(x, y, w, h, title, sub, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.5",
                                fc=color, ec="#333", lw=1.2))
    ax.text(x + w / 2, y + h - 3.2, title, ha="center", va="center", fontsize=8.6, fontweight="bold", color="white")
    ax.text(x + w / 2, y + h / 2 - 2.5, sub, ha="center", va="center", fontsize=7.2, color="white", linespacing=1.35)
def arrow(x1, y1, x2, y2, label=""):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", lw=1.6, color="#333"))
    if label: ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 2.2, label, ha="center", fontsize=6.8, color="#333")
box(1, 28, 17, 15, "INPUT", "JSON dataset\nparcels + road graph\n+ van capacity", "#555555")
box(23, 28, 17, 15, "1. SORT", "Merge sort\n(deadline, priority)\nO(n log n)", "#1f4e79")
box(45, 28, 17, 15, "2. PACK", "0/1 Knapsack DP\nvalue = priority+urgency\nO(n·W)", "#c0504d")
box(67, 28, 17, 15, "3. SHORTEST PATHS", "Dijkstra from depot\nand every stop\nO(k (V+E) log V)", "#2e8b57")
box(67, 5, 17, 15, "4. ROUTE", "Nearest-neighbour TSP\n(+ optional 2-opt)\nO(k²)", "#e08e0b")
box(45, 5, 17, 15, "5. SCHEDULE", "ETA at each stop\ndeadline check\nroute length", "#7b4fa3")
box(23, 5, 17, 15, "OUTPUT", "Loaded parcels\nordered stops\nroad path + km", "#555555")
box(1, 5, 17, 15, "6. NEXT TRIP?", "left-over parcels\nrepeat steps 1-5\nuntil none remain", "#1f4e79")
arrow(18.5, 35.5, 22.5, 35.5); arrow(40.5, 35.5, 44.5, 35.5)
arrow(62.5, 35.5, 66.5, 35.5);  arrow(75.5, 27.5, 75.5, 20.5)
ax.text(77, 24, "stop set", fontsize=6.8, va="center")
arrow(66.5, 12.5, 62.5, 12.5); arrow(44.5, 12.5, 40.5, 12.5); arrow(22.5, 12.5, 18.5, 12.5)
ax.text(43, 1.5, "Runtime of every box is measured (Phase 4);  the left-over parcels feed a new trip.", ha="center", fontsize=7.5, style="italic")
fig.tight_layout(); fig.savefig("outputs/charts/design_flow.png", dpi=170)
