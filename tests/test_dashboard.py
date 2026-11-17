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


def test_findings_filter_by_host(seeded):
    rows = dashboard_app.run_findings(
        "run-demo", "x15_y3_z15", limit=10, offset=0, q="pq.example"
    )
    assert [row["host"] for row in rows] == ["pq.example"]


def test_findings_filter_by_algorithm(seeded):
    rows = dashboard_app.run_findings(
        "run-demo", "x15_y3_z15", limit=10, offset=0, q="MLKEM"
    )
    assert rows
    assert all("MLKEM" in (row["kx_group"] or "") for row in rows)


def test_findings_filter_is_case_insensitive(seeded):
    rows = dashboard_app.run_findings(
        "run-demo", "x15_y3_z15", limit=10, offset=0, q="PQ.EXAMPLE"
    )
    assert [row["host"] for row in rows] == ["pq.example"]


def test_findings_pagination_is_stable(seeded):
    first = dashboard_app.run_findings("run-demo", "x15_y3_z15", limit=1, offset=0)
    second = dashboard_app.run_findings("run-demo", "x15_y3_z15", limit=1, offset=1)
    assert len(first) == 1
    assert len(second) == 1
    assert first[0]["host"] != second[0]["host"]


def test_findings_q_is_passed_through_api(seeded):
    payload = dashboard_app.api_findings(
        run_id="run-demo", scenario="x15_y3_z15", limit=10, offset=0, q="pq"
    )
    assert payload["q"] == "pq"
    assert len(payload["findings"]) == 1


def test_dashboard_index_renders_search_and_pagination_controls(seeded):
    from starlette.requests import Request

    req = Request({"type": "http", "method": "GET", "path": "/", "headers": []})
    resp = dashboard_app.index(req)
    assert resp.status_code == 200
    html = resp.body.decode("utf-8")
    assert 'id="findings-search"' in html
    assert 'id="findings-prev"' in html
    assert 'id="findings-next"' in html
    assert 'id="findings-page-info"' in html


def test_findings_filter_with_pagination(seeded):
    # Both example.com and pq.example match "example"
    first = dashboard_app.run_findings(
        "run-demo", "x15_y3_z15", limit=1, offset=0, q="example"
    )
    second = dashboard_app.run_findings(
        "run-demo", "x15_y3_z15", limit=1, offset=1, q="example"
    )
    assert len(first) == 1
    assert len(second) == 1
    assert first[0]["host"] != second[0]["host"]
    assert "example" in first[0]["host"]
    assert "example" in second[0]["host"]


def test_findings_pagination_beyond_available_rows(seeded):
    rows = dashboard_app.run_findings(
        "run-demo", "x15_y3_z15", limit=10, offset=100, q="example"
    )
    assert rows == []


def test_methodology_page_renders_formula_and_defaults():
    from starlette.requests import Request

    req = Request({"type": "http", "method": "GET", "path": "/methodology", "headers": []})
    resp = dashboard_app.methodology(req)
    assert resp.status_code == 200
    html = resp.body.decode("utf-8")
    assert "X + Y" in html
    assert "Mosca" in html
    assert "x15_y3_z15" in html
    assert "vulnerable" in html
    assert "hybrid" in html
    assert "resistant" in html
    assert "weakened" in html
    assert "Handshake Only" in html


def test_accessibility_features_in_html_and_css(seeded):
    from pathlib import Path
    from starlette.requests import Request

    req = Request({"type": "http", "method": "GET", "path": "/", "headers": []})
    resp = dashboard_app.index(req)
    assert resp.status_code == 200
    html = resp.body.decode("utf-8")
    assert "<caption" in html
    assert 'for="run-select"' in html
    assert 'for="scenario-select"' in html
    assert 'for="findings-search"' in html

    m_resp = dashboard_app.methodology(req)
    assert m_resp.status_code == 200
    m_html = m_resp.body.decode("utf-8")
    assert "<caption" in m_html

    css_path = Path(__file__).parent.parent / "dashboard" / "static" / "style.css"
    css = css_path.read_text(encoding="utf-8")
    assert ":focus-visible" in css
    assert "border-color" in css


def test_api_findings_pagination_parameters(seeded):
    first = dashboard_app.api_findings(
        run_id="run-demo", scenario="x15_y3_z15", limit=1, offset=0
    )
    assert first["limit"] == 1
    assert first["offset"] == 0
    assert len(first["findings"]) == 1

    second = dashboard_app.api_findings(
        run_id="run-demo", scenario="x15_y3_z15", limit=1, offset=1
    )
    assert second["limit"] == 1
    assert second["offset"] == 1
    assert len(second["findings"]) == 1
    assert first["findings"][0]["host"] != second["findings"][0]["host"]

    empty = dashboard_app.api_findings(
        run_id="run-demo", scenario="x15_y3_z15", limit=10, offset=100
    )
    assert empty["findings"] == []


def test_api_sensitivity_response_shape(seeded):
    payload = dashboard_app.api_sensitivity(run_id="run-demo")
    required_keys = {
        "run_id",
        "hosts",
        "flips",
        "naive_high",
        "optimistic",
        "pessimistic",
        "per_scenario",
        "classes",
    }
    assert required_keys.issubset(payload.keys())
    assert payload["run_id"] == "run-demo"
    assert isinstance(payload["hosts"], int)
    assert isinstance(payload["flips"], int)
    assert isinstance(payload["naive_high"], int)
    assert isinstance(payload["per_scenario"], dict)
    assert isinstance(payload["classes"], dict)
    assert len(payload["per_scenario"]) > 0

    # Ensure JSON serializable
    dumped = json.dumps(payload)
    assert "run-demo" in dumped


def test_unknown_run_raises_404_on_all_endpoints(seeded):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_summary:
        dashboard_app.api_summary(run_id="non-existent-run")
    assert exc_summary.value.status_code == 404

    with pytest.raises(HTTPException) as exc_findings:
        dashboard_app.api_findings(run_id="non-existent-run")
    assert exc_findings.value.status_code == 404

    with pytest.raises(HTTPException) as exc_sensitivity:
        dashboard_app.api_sensitivity(run_id="non-existent-run")
    assert exc_sensitivity.value.status_code == 404





