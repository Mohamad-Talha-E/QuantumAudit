"""Database layer for QuantumAudit.

Two separate tables:

* ``findings`` -- one row per host we scanned. Raw handshake facts only.
* ``scores``   -- one row per finding *per scenario*. Risk verdicts.

The original guide used a single ``reason`` column for two different things
(why a scan failed, and why a host scored high). That collision is the exact
"schema drift" the guide warns about, so the two are split here.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_DB = "data/quantumaudit.db"

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS findings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      TEXT    NOT NULL,
    host        TEXT    NOT NULL,
    port        INTEGER NOT NULL DEFAULT 443,
    profile     TEXT    NOT NULL DEFAULT 'public',
    scan_time   TEXT    NOT NULL,
    protocol    TEXT,
    cipher      TEXT,
    kx_group    TEXT,
    cert_alg    TEXT,
    key_size    INTEGER,
    sig_alg     TEXT,
    cert_expiry TEXT,
    hybrid_flag INTEGER NOT NULL DEFAULT 0,
    status      TEXT    NOT NULL,
    error       TEXT,
    UNIQUE (run_id, host, port)
);

CREATE TABLE IF NOT EXISTS scores (
    finding_id       INTEGER NOT NULL REFERENCES findings(id) ON DELETE CASCADE,
    scenario         TEXT    NOT NULL,
    shelf_life_years INTEGER NOT NULL,
    migration_years  INTEGER NOT NULL,
    quantum_years    INTEGER NOT NULL,
    alg_class        TEXT    NOT NULL,
    score_naive      TEXT    NOT NULL,
    score_contextual TEXT    NOT NULL,
    reason           TEXT    NOT NULL,
    migration_step   TEXT    NOT NULL,
    PRIMARY KEY (finding_id, scenario)
);

CREATE TABLE IF NOT EXISTS bench (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      TEXT    NOT NULL,
    algo        TEXT    NOT NULL,
    op          TEXT    NOT NULL,
    ops_per_s   REAL,
    mean_ms     REAL,
    bytes       INTEGER,
    constrained INTEGER NOT NULL DEFAULT 0,
    ts          TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_findings_host     ON findings(host);
CREATE INDEX IF NOT EXISTS idx_findings_run      ON findings(run_id);
CREATE INDEX IF NOT EXISTS idx_scores_scenario   ON scores(scenario);
"""


def connect(path: str = DEFAULT_DB) -> sqlite3.Connection:
    """Open (and create if needed) the database file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path: str = DEFAULT_DB) -> sqlite3.Connection:
    """Create the schema if it is not there yet and return a connection."""
    conn = connect(path)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def insert_finding(conn: sqlite3.Connection, run_id: str, rec: dict) -> int | None:
    """Insert or update one scan record.

    Every column is supplied explicitly. The guide's version used named
    parameters but left keys missing on the error path, which raised
    ``ProgrammingError`` -- i.e. it crashed on exactly the failed scans it
    told us to keep.

    A repeat scan of the same host under the same ``run_id`` updates the
    existing row rather than being silently ignored, so re-running an
    experiment after a fix actually refreshes the data.
    """
    row = {
        "run_id": run_id,
        "host": rec.get("host"),
        "port": rec.get("port", 443),
        "profile": rec.get("profile", "public"),
        "scan_time": rec.get("scan_time"),
        "protocol": rec.get("protocol"),
        "cipher": rec.get("cipher"),
        "kx_group": rec.get("kx_group"),
        "cert_alg": rec.get("cert_alg"),
        "key_size": rec.get("key_size"),
        "sig_alg": rec.get("sig_alg"),
        "cert_expiry": rec.get("cert_expiry"),
        "hybrid_flag": int(rec.get("hybrid_flag") or 0),
        "status": rec.get("status", "ok"),
        "error": rec.get("error"),
    }
    conn.execute(
        """
        INSERT INTO findings
            (run_id, host, port, profile, scan_time, protocol, cipher,
             kx_group, cert_alg, key_size, sig_alg, cert_expiry,
             hybrid_flag, status, error)
        VALUES
            (:run_id, :host, :port, :profile, :scan_time, :protocol, :cipher,
             :kx_group, :cert_alg, :key_size, :sig_alg, :cert_expiry,
             :hybrid_flag, :status, :error)
        ON CONFLICT (run_id, host, port) DO UPDATE SET
            profile     = excluded.profile,
            scan_time   = excluded.scan_time,
            protocol    = excluded.protocol,
            cipher      = excluded.cipher,
            kx_group    = excluded.kx_group,
            cert_alg    = excluded.cert_alg,
            key_size    = excluded.key_size,
            sig_alg     = excluded.sig_alg,
            cert_expiry = excluded.cert_expiry,
            hybrid_flag = excluded.hybrid_flag,
            status      = excluded.status,
            error       = excluded.error
        """,
        row,
    )
    conn.commit()
    found = conn.execute(
        "SELECT id FROM findings WHERE run_id = ? AND host = ? AND port = ?",
        (row["run_id"], row["host"], row["port"]),
    ).fetchone()
    return found["id"] if found else None
