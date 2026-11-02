"""Tests for the database layer."""

from __future__ import annotations

from scanner.db import init_db, insert_finding


def finding(**overrides) -> dict:
    base = {
        "host": "example.com",
        "port": 443,
        "profile": "public",
        "scan_time": "2026-01-01T00:00:00+00:00",
        "protocol": "TLSv1.3",
        "cipher": "TLS_AES_256_GCM_SHA384",
        "kx_group": "X25519",
        "cert_alg": "RSA",
        "key_size": 2048,
        "sig_alg": "sha256WithRSAEncryption",
        "cert_expiry": "2027-01-01T00:00:00+00:00",
        "hybrid_flag": 0,
        "status": "ok",
        "error": None,
    }
    base.update(overrides)
    return base


def test_insert_returns_row_id(db_path):
    conn = init_db(db_path)
    row_id = insert_finding(conn, "run-1", finding())
    assert isinstance(row_id, int) and row_id > 0
    conn.close()


def test_error_rows_are_stored_not_crashed(db_path):
    """The guide's insert crashed on failed scans; this must not."""
    conn = init_db(db_path)
    row_id = insert_finding(
        conn,
        "run-1",
        finding(protocol=None, cipher=None, kx_group=None, cert_alg=None,
                key_size=None, sig_alg=None, cert_expiry=None,
                status="error", error="TimeoutError: timed out"),
    )
    assert row_id is not None
    row = conn.execute("SELECT * FROM findings WHERE id = ?", (row_id,)).fetchone()
    assert row["status"] == "error"
    assert "timed out" in row["error"]
    conn.close()


def test_rescan_updates_instead_of_duplicating(db_path):
    conn = init_db(db_path)
    first = insert_finding(conn, "run-1", finding(kx_group="X25519"))
    second = insert_finding(conn, "run-1", finding(kx_group="X25519MLKEM768", hybrid_flag=1))

    assert first == second
    count = conn.execute("SELECT COUNT(*) FROM findings").fetchone()[0]
    assert count == 1
    row = conn.execute("SELECT * FROM findings WHERE id = ?", (first,)).fetchone()
    assert row["kx_group"] == "X25519MLKEM768"
    assert row["hybrid_flag"] == 1
    conn.close()


def test_same_host_in_different_runs_is_two_rows(db_path):
    conn = init_db(db_path)
    insert_finding(conn, "run-a", finding())
    insert_finding(conn, "run-b", finding())
    count = conn.execute("SELECT COUNT(*) FROM findings").fetchone()[0]
    assert count == 2
    conn.close()


def test_schema_has_separate_findings_and_scores_tables(db_path):
    conn = init_db(db_path)
    names = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    assert {"findings", "scores", "bench"} <= names
    conn.close()
