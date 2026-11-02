"""FastAPI dashboard for QuantumAudit.

Run it inside the toolbox container::

    docker compose run --rm --service-ports tools \
        uvicorn dashboard.app:app --host 0.0.0.0 --port 8000

or use the ``dashboard`` service in ``docker-compose.yml``.

Pages and endpoints:

* ``/``                    HTML dashboard
* ``/api/runs``            available scan runs
* ``/api/summary``         counts, distributions and chart names
* ``/api/findings``        the scan table (paginated)
* ``/api/sensitivity``     E6 table for one run
"""

from __future__ import annotations

import os
import sqlite3

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from dashboard import charts
from scanner.db import DEFAULT_DB
from scoring.mosca import scenario_name
from scoring.sensitivity import build_table

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.environ.get("QUANTUMAUDIT_DB", DEFAULT_DB)
DEFAULT_SCENARIO = scenario_name(15, 3, 15)

app = FastAPI(title="QuantumAudit", version="1.0")
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static",
)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


def _connect() -> sqlite3.Connection:
    if not os.path.exists(DB_PATH):
        raise HTTPException(
            status_code=404,
            detail=f"Database {DB_PATH} not found. Run a scan first.",
        )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def list_runs() -> list[dict]:
    """Every run that has at least one finding."""
    conn = _connect()
    rows = conn.execute(
        """
        SELECT run_id,
               COUNT(*)                       AS hosts,
               SUM(status = 'ok')             AS ok,
               MIN(scan_time)                 AS started,
               MAX(scan_time)                 AS finished
        FROM findings
        GROUP BY run_id
        ORDER BY finished DESC
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def run_summary(run_id: str, scenario: str = DEFAULT_SCENARIO) -> dict:
    """Everything the dashboard needs about one run, JSON-safe."""
    conn = _connect()
    base = conn.execute(
        """
        SELECT COUNT(*)                  AS hosts,
               SUM(status = 'ok')        AS ok,
               SUM(status = 'error')     AS failed,
               SUM(hybrid_flag = 1)      AS hybrid,
               MIN(scan_time)            AS started,
               MAX(scan_time)            AS finished
        FROM findings WHERE run_id = ?
        """,
        (run_id,),
    ).fetchone()

    if not base or not base["hosts"]:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Run {run_id!r} not found")

    kx_rows = conn.execute(
        """
        SELECT COALESCE(kx_group, 'unknown') AS value, COUNT(*) AS count
        FROM findings WHERE run_id = ? AND status = 'ok'
        GROUP BY value ORDER BY count DESC
        """,
        (run_id,),
    ).fetchall()
    cert_rows = conn.execute(
        """
        SELECT COALESCE(cert_alg, 'unknown') AS value, COUNT(*) AS count
        FROM findings WHERE run_id = ? AND status = 'ok'
        GROUP BY value ORDER BY count DESC
        """,
        (run_id,),
    ).fetchall()
    proto_rows = conn.execute(
        """
        SELECT COALESCE(protocol, 'unknown') AS value, COUNT(*) AS count
        FROM findings WHERE run_id = ? AND status = 'ok'
        GROUP BY value ORDER BY count DESC
        """,
        (run_id,),
    ).fetchall()

    verdict_rows = conn.execute(
        """
        SELECT s.score_contextual AS level, COUNT(*) AS count
        FROM scores s JOIN findings f ON f.id = s.finding_id
        WHERE f.run_id = ? AND s.scenario = ?
        GROUP BY level
        """,
        (run_id, scenario),
    ).fetchall()
    naive_rows = conn.execute(
        """
        SELECT s.score_naive AS level, COUNT(*) AS count
        FROM scores s JOIN findings f ON f.id = s.finding_id
        WHERE f.run_id = ? AND s.scenario = ?
        GROUP BY level
        """,
        (run_id, scenario),
    ).fetchall()

    classes_rows = conn.execute(
        """
        SELECT s.alg_class AS value, COUNT(*) AS count
        FROM scores s JOIN findings f ON f.id = s.finding_id
        WHERE f.run_id = ? AND s.scenario = ?
        GROUP BY value ORDER BY count DESC
        """,
        (run_id, scenario),
    ).fetchall()

    scenarios = [
        row["scenario"]
        for row in conn.execute(
            """
            SELECT DISTINCT s.scenario
            FROM scores s JOIN findings f ON f.id = s.finding_id
            WHERE f.run_id = ? ORDER BY s.scenario
            """,
            (run_id,),
        ).fetchall()
    ]
    conn.close()

    hosts = base["hosts"] or 0
    ok = base["ok"] or 0
    hybrid = base["hybrid"] or 0

    return {
        "run_id": run_id,
        "scenario": scenario,
        "scenarios": scenarios,
        "hosts": hosts,
        "ok": ok,
        "failed": base["failed"] or 0,
        "hybrid": hybrid,
        "pq_key_exchange_pct": round(100.0 * hybrid / ok, 1) if ok else 0.0,
        "started": base["started"],
        "finished": base["finished"],
        "kx_groups": {row["value"]: row["count"] for row in kx_rows},
        "cert_algs": {row["value"]: row["count"] for row in cert_rows},
        "protocols": {row["value"]: row["count"] for row in proto_rows},
        "contextual": {row["level"]: row["count"] for row in verdict_rows},
        "naive": {row["level"]: row["count"] for row in naive_rows},
        "classes": {row["value"]: row["count"] for row in classes_rows},
    }


def run_findings(run_id: str, scenario: str, limit: int, offset: int) -> list[dict]:
    conn = _connect()
    rows = conn.execute(
        """
        SELECT f.host, f.port, f.protocol, f.cipher, f.kx_group, f.cert_alg,
               f.key_size, f.hybrid_flag, f.status, f.error,
               s.alg_class, s.score_contextual, s.score_naive,
               s.reason, s.migration_step
        FROM findings f
        LEFT JOIN scores s
               ON s.finding_id = f.id AND s.scenario = ?
        WHERE f.run_id = ?
        ORDER BY
            CASE s.score_contextual
                WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END,
            f.host
        LIMIT ? OFFSET ?
        """,
        (scenario, run_id, limit, offset),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    try:
        runs = list_runs()
    except HTTPException:
        runs = []
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"runs": runs, "default_scenario": DEFAULT_SCENARIO},
    )


@app.get("/api/runs")
def api_runs() -> dict:
    return {"runs": list_runs()}


@app.get("/api/summary")
def api_summary(
    run_id: str = Query(..., description="Run identifier"),
    scenario: str = Query(DEFAULT_SCENARIO),
) -> dict:
    summary = run_summary(run_id, scenario)
    try:
        table = build_table(run_id, db=DB_PATH)
    except Exception:
        table = {"per_scenario": {}, "hosts": summary["hosts"]}
    summary["charts"] = charts.build_all(run_id, summary, table)
    return summary


@app.get("/api/findings")
def api_findings(
    run_id: str,
    scenario: str = Query(DEFAULT_SCENARIO),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> dict:
    return {
        "run_id": run_id,
        "scenario": scenario,
        "limit": limit,
        "offset": offset,
        "findings": run_findings(run_id, scenario, limit, offset),
    }


@app.get("/api/sensitivity")
def api_sensitivity(run_id: str) -> dict:
    table = build_table(run_id, db=DB_PATH)
    return {
        "run_id": run_id,
        "hosts": table["hosts"],
        "flips": table["flips"],
        "naive_high": table["naive_high"],
        "optimistic": table["optimistic"],
        "pessimistic": table["pessimistic"],
        "per_scenario": {
            key: dict(counts) for key, counts in table["per_scenario"].items()
        },
        "classes": dict(table["classes"]),
    }
