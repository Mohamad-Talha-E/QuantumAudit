"""E6 -- sensitivity analysis.

Question: how much do risk verdicts move when the assumptions move?

For every host we compute the verdict under each quantum horizon (10/15/20
years) and shelf life, then count how many hosts change class between the
optimistic and pessimistic scenario. That flip count is the headline number.
"""

from __future__ import annotations

from collections import Counter

from scanner.db import DEFAULT_DB, init_db
from scoring.mosca import HORIZONS, MIGRATION_STEP, SHELF_LIVES, naive_score, score
from scoring.rules import classify


def build_table(
    run_id: str,
    db: str = DEFAULT_DB,
    horizons=HORIZONS,
    shelf_lives=SHELF_LIVES,
    migration_years: int = 3,
) -> dict:
    """Return per-scenario distributions plus flip counts."""
    conn = init_db(db)
    rows = conn.execute(
        "SELECT * FROM findings WHERE run_id = ? AND status = 'ok'", (run_id,)
    ).fetchall()
    conn.close()

    records = [dict(row) for row in rows]
    per_scenario: dict[str, Counter] = {}
    verdicts: dict[str, list[str]] = {}

    for shelf in shelf_lives:
        for horizon in horizons:
            key = f"x{shelf}_z{horizon}"
            counts: Counter = Counter()
            column: list[str] = []
            for record in records:
                level, _, _ = score(
                    record,
                    shelf_life_years=shelf,
                    migration_years=migration_years,
                    quantum_years=horizon,
                )
                counts[level] += 1
                column.append(level)
            per_scenario[key] = counts
            verdicts[key] = column

    # Flips between the most optimistic and most pessimistic scenario.
    optimistic = verdicts.get(f"x{min(shelf_lives)}_z{max(horizons)}", [])
    pessimistic = verdicts.get(f"x{max(shelf_lives)}_z{min(horizons)}", [])
    flips = sum(1 for a, b in zip(optimistic, pessimistic) if a != b)

    naive_high = sum(1 for r in records if naive_score(r)[0] == "high")
    classes = Counter(classify(r) for r in records)

    return {
        "hosts": len(records),
        "per_scenario": per_scenario,
        "flips": flips,
        "naive_high": naive_high,
        "classes": classes,
        "optimistic": f"x{min(shelf_lives)}_z{max(horizons)}",
        "pessimistic": f"x{max(shelf_lives)}_z{min(horizons)}",
        "migration_years": migration_years,
        "migration_steps": MIGRATION_STEP,
    }


def to_markdown(table: dict) -> str:
    """Render the sensitivity table as Markdown for results.md."""
    lines = [
        "### E6 -- sensitivity analysis",
        "",
        f"Hosts scored: **{table['hosts']}**  ",
        f"Migration time assumed: **{table['migration_years']} years**  ",
        f"Verdict changes between `{table['optimistic']}` and "
        f"`{table['pessimistic']}`: **{table['flips']}**  ",
        f"Hosts the naive rule calls high: **{table['naive_high']}**",
        "",
        "| shelf life / horizon | low | medium | high |",
        "|---|---|---|---|",
    ]
    for key, counts in sorted(table["per_scenario"].items()):
        lines.append(
            f"| {key} | {counts.get('low', 0)} | "
            f"{counts.get('medium', 0)} | {counts.get('high', 0)} |"
        )
    lines.append("")
    lines.append("| algorithm class | hosts |")
    lines.append("|---|---|")
    for name, count in table["classes"].most_common():
        lines.append(f"| {name} | {count} |")
    lines.append("")
    return "\n".join(lines)
