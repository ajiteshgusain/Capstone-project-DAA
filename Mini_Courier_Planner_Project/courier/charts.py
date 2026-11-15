"""Matplotlib charts used by the benchmark and the report."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PALETTE = ["#1f4e79", "#c0504d", "#2e8b57", "#e08e0b", "#7b4fa3", "#555555"]


def _style(ax, title, xl, yl):
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.set_xlabel(xl); ax.set_ylabel(yl)
    ax.grid(True, alpha=0.3)


def route_map(problem, trip, path, title=None):
    fig, ax = plt.subplots(figsize=(8, 6))
    for u, v, w in problem.graph.edges():
        a, b = problem.nodes[u], problem.nodes[v]
        ax.plot([a.x, b.x], [a.y, b.y], color="#bbbbbb", lw=0.8, zorder=1)
        if len(problem.graph) <= 12:
            ax.text((a.x + b.x) / 2, (a.y + b.y) / 2, f"{w:g}", fontsize=7, color="#777",
                    ha="center", va="center", bbox=dict(fc="white", ec="none", pad=0.5))
    for i, (u, v) in enumerate(zip(trip.route, trip.route[1:])):
        a, b = problem.nodes[u], problem.nodes[v]
        ax.annotate("", xy=(b.x, b.y), xytext=(a.x, a.y), zorder=3,
                    arrowprops=dict(arrowstyle="->", color=PALETTE[1], lw=1.8,
                                    shrinkA=6, shrinkB=6, connectionstyle="arc3,rad=0.12"))
    stops = set(trip.stops)
    for n in problem.nodes.values():
        if n.id == problem.depot:
            ax.scatter(n.x, n.y, s=220, marker="s", color=PALETTE[0], zorder=4)
        elif n.id in stops:
            ax.scatter(n.x, n.y, s=90, color=PALETTE[2], zorder=4)
        else:
            ax.scatter(n.x, n.y, s=28, color="#999999", zorder=2)
        if len(problem.graph) <= 12 or n.id in stops or n.id == problem.depot:
            ax.text(n.x, n.y + 0.45 if len(problem.graph) <= 12 else n.y + 1.6,
                    str(n.id) if len(problem.graph) > 12 else f"{n.id}: {n.name}",
                    fontsize=8 if len(problem.graph) <= 12 else 6.5, ha="center", zorder=5)
    order = {s: i for i, s in enumerate(trip.tour[1:-1], 1)}
    ax.set_title(title or f"{problem.name}: delivery route ({trip.route_km:.1f} km, "
                 f"{len(trip.stops)} stops)", fontsize=11, fontweight="bold", pad=22)
    ax.margins(0.1); ax.set_aspect("equal"); ax.axis("off")
    fig.tight_layout(); fig.savefig(path, dpi=160); plt.close(fig)


def line_chart(path, title, xl, yl, series, logx=False, logy=False, figsize=(7.5, 4.8)):
    """series: {label: (xs, ys)}"""
    fig, ax = plt.subplots(figsize=figsize)
    for i, (lab, (xs, ys)) in enumerate(series.items()):
        ax.plot(xs, ys, marker="o", ms=4, lw=1.8, label=lab, color=PALETTE[i % len(PALETTE)])
    if logx: ax.set_xscale("log")
    if logy: ax.set_yscale("log")
    _style(ax, title, xl, yl)
    ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(path, dpi=160); plt.close(fig)


def terminal_image(text, path, title="Terminal output", width=110):
    lines = text.rstrip("\n").split("\n")
    h = max(2.0, 0.158 * len(lines) + 0.9)
    fig = plt.figure(figsize=(width * 0.108, h), facecolor="#1e1e1e")
    fig.text(0.012, 1 - 0.35 / h, f"\u25CF \u25CF \u25CF   {title}", color="#9cdcfe",
             fontsize=8.5, family="monospace", va="center")
    fig.text(0.012, 1 - 0.75 / h, "\n".join(lines), color="#d4d4d4", fontsize=7.6,
             family="monospace", va="top", linespacing=1.18)
    fig.savefig(path, dpi=150, facecolor=fig.get_facecolor()); plt.close(fig)
