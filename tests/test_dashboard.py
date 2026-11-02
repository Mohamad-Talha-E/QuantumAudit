"""Tests for the dashboard data layer.

The dashboard must never leak a non-JSON value (numpy int, sqlite Row, ...),
so the main assertion is that the payload round-trips through ``json.dumps``.
"""

from __future__ import annotations

import json

import pytest

from dashboard import app as dashboard_app
from scanner.db import init_db, insert_finding
from scoring.score_db import score_run


def seed(db_path: str) -> None:
    conn = init_db(db_path)
    rows = [
        ("example.com", "RSA", "X25519", 0),
        ("pq.example", "RSA", "X25519MLKEM768", 1),
        ("broken.example", None, None, 0),
    ]
    for index, (host, cert, group, hybrid) in enumerate(rows):
        insert_finding(
            conn,
            "run-demo",
            {
                "host": host,
                "port": 443,
                "profile": "public",
                "scan_time": f"2026-01-0{index + 1}T00:00:00+00:00",
                "protocol": "TLSv1.3" if cert else None,
                "cipher": "TLS_AES_256_GCM_SHA384" if cert else None,
                "kx_group": group,
                "cert_alg": cert,
                "key_size": 2048 if cert else None,
                "sig_alg": "sha256WithRSAEncryption" if cert else None,
                "cert_expiry": None,
                "hybrid_flag": hybrid,
                "status": "ok" if cert else "error",
                "error": None if cert else "TimeoutError: timed out",
            },
        )
    conn.close()
    score_run("run-demo", db=db_path)


@pytest.fixture()
def seeded(db_path, monkeypatch):
    seed(db_path)
    monkeypatch.setattr(dashboard_app, "DB_PATH", db_path)
    return db_path


def test_summary_is_json_safe(seeded):
    summary = dashboard_app.run_summary("run-demo")
    text = json.dumps(summary)  # raises if any value is not JSON-native
    assert "run-demo" in text


def test_summary_counts(seeded):
    summary = dashboard_app.run_summary("run-demo")
    assert summary["hosts"] == 3
    assert summary["ok"] == 2
    assert summary["failed"] == 1
    assert summary["hybrid"] == 1
    assert summary["pq_key_exchange_pct"] == 50.0


def test_summary_verdicts(seeded):
    summary = dashboard_app.run_summary("run-demo")
    assert summary["contextual"]["high"] >= 1
    assert summary["contextual"]["low"] >= 1
    assert summary["naive"]["high"] >= 1


def test_findings_are_sorted_high_first(seeded):
    rows = dashboard_app.run_findings("run-demo", "x15_y3_z15", limit=10, offset=0)
    assert len(rows) == 3
    assert rows[0]["score_contextual"] == "high"
    assert rows[-1]["score_contextual"] in ("low", "medium", None)


def test_unknown_run_raises(seeded):
    from fastapi import HTTPException

    with pytest.raises(HTTPException):
        dashboard_app.run_summary("does-not-exist")


def test_runs_list(seeded):
    runs = dashboard_app.list_runs()
    assert len(runs) == 1
    assert runs[0]["run_id"] == "run-demo"
    assert runs[0]["hosts"] == 3
