"""Chart generation for the dashboard.

Matplotlib only -- no pandas, no seaborn. Each function returns the path of a
PNG file under ``dashboard/static/charts``. The Agg backend is forced so the
code works in a container with no display.
"""

from __future__ import annotations

import os
from collections import Counter

import matplotlib

matplotlib.use("Agg")  # must come before pyplot is imported

import matplotlib.pyplot as plt  # noqa: E402

CHART_DIR = os.path.join(os.path.dirname(__file__), "static", "charts")

#: Colours for the three risk levels, reused across charts.
RISK_COLOURS = {"low": "#2e7d32", "medium": "#ef6c00", "high": "#c62828"}
PALETTE = ["#1565c0", "#00838f", "#6a1b9a", "#ad1457", "#4e342e", "#37474f"]


def _ensure_dir() -> str:
    os.makedirs(CHART_DIR, exist_ok=True)
    return CHART_DIR


def _finish(fig, name: str) -> str:
    path = os.path.join(_ensure_dir(), name)
    fig.tight_layout()
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return path


def risk_distribution(contextual: dict[str, int], naive: dict[str, int], name: str) -> str:
    """Grouped bars: contextual verdicts next to the naive baseline."""
    levels = ["low", "medium", "high"]
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    width = 0.36
    positions = range(len(levels))

    contextual_values = [contextual.get(level, 0) for level in levels]
    naive_values = [naive.get(level, 0) for level in levels]

    ax.bar(
        [p - width / 2 for p in positions],
        contextual_values,
        width,
        label="Contextual (Mosca)",
        color="#1565c0",
    )
    ax.bar(
        [p + width / 2 for p in positions],
        naive_values,
        width,
        label="Naive rule",
        color="#90a4ae",
    )
    ax.set_xticks(list(positions))
    ax.set_xticklabels([level.title() for level in levels])
    ax.set_ylabel("Hosts")
    ax.set_title("Risk verdicts: contextual vs naive")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    return _finish(fig, name)


def category_bar(counts: dict[str, int], title: str, xlabel: str, name: str) -> str:
    """Horizontal bar chart for a categorical distribution."""
    items = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:10]
    labels = [label or "unknown" for label, _ in items][::-1]
    values = [value for _, value in items][::-1]

    height = max(2.4, 0.42 * len(items) + 1.2)
    fig, ax = plt.subplots(figsize=(6.4, height))
    bars = ax.barh(labels, values, color=PALETTE * 3)
    ax.bar_label(bars, padding=3, fontsize=8)
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    ax.spines[["top", "right"]].set_visible(False)
    ax.margins(x=0.12)
    return _finish(fig, name)


def sensitivity_heatmap(table: dict, name: str) -> str:
    """Heatmap of the share of hosts rated high across scenarios."""
    scenarios = sorted(table["per_scenario"])
    hosts = max(table["hosts"], 1)

    shelves = sorted({int(key.split("_")[0][1:]) for key in scenarios})
    horizons = sorted({int(key.split("_")[1][1:]) for key in scenarios})

    grid = []
    for shelf in shelves:
        row = []
        for horizon in horizons:
            counts = table["per_scenario"].get(f"x{shelf}_z{horizon}", {})
            row.append(100.0 * counts.get("high", 0) / hosts)
        grid.append(row)

    fig, ax = plt.subplots(figsize=(5.6, 0.6 * len(shelves) + 2.0))
    image = ax.imshow(grid, cmap="YlOrRd", vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(len(horizons)))
    ax.set_xticklabels([f"{h}y" for h in horizons])
    ax.set_yticks(range(len(shelves)))
    ax.set_yticklabels([f"{s}y shelf" for s in shelves])
    ax.set_xlabel("Quantum horizon (Z)")
    ax.set_title("Share of hosts rated HIGH (%)")

    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            ax.text(
                column_index,
                row_index,
                f"{value:.0f}",
                ha="center",
                va="center",
                fontsize=9,
                color="black" if value < 60 else "white",
            )
    fig.colorbar(image, ax=ax, label="% high")
    return _finish(fig, name)


def build_all(run_id: str, summary: dict, table: dict) -> dict[str, str]:
    """Generate every chart for one run and return ``{key: path}``."""
    safe = run_id.replace("/", "_")
    charts = {
        "risk": risk_distribution(
            summary["contextual"], summary["naive"], f"{safe}_risk.png"
        ),
        "kx": category_bar(
            summary["kx_groups"],
            "Negotiated key-exchange groups",
            "Hosts",
            f"{safe}_kx.png",
        ),
        "certs": category_bar(
            summary["cert_algs"],
            "Certificate algorithms",
            "Hosts",
            f"{safe}_certs.png",
        ),
    }
    if table.get("per_scenario"):
        charts["sensitivity"] = sensitivity_heatmap(table, f"{safe}_sensitivity.png")
    return {key: os.path.basename(path) for key, path in charts.items()}


def counter(values) -> dict[str, int]:
    """Count values, mapping ``None`` to ``unknown``."""
    return dict(Counter(str(value) if value else "unknown" for value in values))
