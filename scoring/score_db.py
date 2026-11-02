"""Apply the scorers to stored scan results and save the verdicts."""

from __future__ import annotations

from scanner.db import DEFAULT_DB, init_db
from scoring.mosca import (
    DEFAULT_HORIZON,
    DEFAULT_MIGRATION,
    DEFAULT_SHELF_LIFE,
    naive_score,
    scenario_name,
    score,
)
from scoring.rules import classify


def score_run(
    run_id: str,
    db: str = DEFAULT_DB,
    shelf_life_years: int = DEFAULT_SHELF_LIFE,
    migration_years: int = DEFAULT_MIGRATION,
    quantum_years: int = DEFAULT_HORIZON,
    only_ok: bool = True,
) -> int:
    """Score every finding in a run. Returns the number of rows written."""
    conn = init_db(db)
    where = "WHERE run_id = ?" + (" AND status = 'ok'" if only_ok else "")
    rows = conn.execute(f"SELECT * FROM findings {where}", (run_id,)).fetchall()

    scenario = scenario_name(shelf_life_years, migration_years, quantum_years)
    written = 0

    for row in rows:
        record = dict(row)
        level, reason, step = score(
            record,
            shelf_life_years=shelf_life_years,
            migration_years=migration_years,
            quantum_years=quantum_years,
        )
        naive, _, _ = naive_score(record)

        conn.execute(
            """
            INSERT INTO scores
                (finding_id, scenario, shelf_life_years, migration_years,
                 quantum_years, alg_class, score_naive, score_contextual,
                 reason, migration_step)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (finding_id, scenario) DO UPDATE SET
                alg_class        = excluded.alg_class,
                score_naive      = excluded.score_naive,
                score_contextual = excluded.score_contextual,
                reason           = excluded.reason,
                migration_step   = excluded.migration_step
            """,
            (
                record["id"],
                scenario,
                shelf_life_years,
                migration_years,
                quantum_years,
                classify(record),
                naive,
                level,
                reason,
                step,
            ),
        )
        written += 1

    conn.commit()
    conn.close()
    return written


def score_all_scenarios(
    run_id: str,
    db: str = DEFAULT_DB,
    horizons=(10, 15, 20),
    shelf_lives=(15,),
    migration_years: int = DEFAULT_MIGRATION,
) -> int:
    """Score a run across every horizon/shelf-life combination (E6 input)."""
    total = 0
    for shelf in shelf_lives:
        for horizon in horizons:
            total += score_run(
                run_id,
                db=db,
                shelf_life_years=shelf,
                migration_years=migration_years,
                quantum_years=horizon,
            )
    return total
