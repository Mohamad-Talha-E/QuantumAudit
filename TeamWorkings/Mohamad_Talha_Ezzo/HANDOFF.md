# HANDOFF — Mohamad Talha Ezzo

> **How to use this file**
>
> 1. Open a terminal in the `QuantumAudit` folder.
> 2. Run `git checkout build/full-system` and `git pull origin build/full-system`.
> 3. Start Claude Code (or any coding agent) in that folder.
> 4. Paste this **entire file** as the first message.
> 5. Review the diff, run the tests, and commit under your own name.
>
> The agent has the exact change, the test and the commands. Nothing is left
> to guess.

**Member:** Mohamad Talha Ezzo (23000488)
**Area:** Scanner and Data Engineering
**Git identity:** `Mohamad Talha Ezzo <talhaezzo2006@gmail.com>`
**Branch:** `talha/schema-docs`
**Task:** T5 — Document the data model
**Time budget:** about 30 minutes

---

## 1. What QuantumAudit is

QuantumAudit scans TLS servers, records which cryptography they use, and scores
the risk that a future quantum computer breaks it. The scanner writes raw facts
to a SQLite database. The scorer reads those facts and writes verdicts. The
dashboard shows both. Everything runs in Docker.

## 2. What you own

You own `scanner/` and the scanner tests. For this task you will touch only:

- `scanner/SCHEMA.md` — **new file**
- `tests/test_schema_docs.py` — **new file**
- `TeamWorkings/Mohamad_Talha_Ezzo/TASKS.md` — to record the commit

Do **not** edit `scoring/`, `lab/`, `dashboard/` or another member's files.

## 3. The task in plain language

The database has three tables: `findings`, `scores` and `bench`. The only
description of them today is the SQL inside `scanner/db.py`. Write a short
`scanner/SCHEMA.md` that a new team member can read, and add a test that fails
if the document ever falls out of step with the code.

## 4. Read these first

- `scanner/db.py`, lines 20–72 — the real schema.
- `tests/conftest.py` — the `db_path` fixture you will use.
- `scanner/SCHEMA.md` does not exist yet; you will create it.

## 5. Create `scanner/SCHEMA.md`

Create the file with exactly this content:

````markdown
# Database schema

The schema is defined in `scanner/db.py`. The database is SQLite. There are
three tables. A generated database lives in `data/` and is never committed.

## `findings`

One row per host per scan run. It stores raw handshake facts only: what the
server actually negotiated. It never stores payload.

| column | type | meaning |
|---|---|---|
| `id` | INTEGER | primary key |
| `run_id` | TEXT | experiment name, for example `e2-tranco` |
| `host` | TEXT | hostname or IP address that was scanned |
| `port` | INTEGER | TCP port, default 443 |
| `profile` | TEXT | `public` or `lab` (which trust store was used) |
| `scan_time` | TEXT | UTC timestamp of the scan |
| `protocol` | TEXT | negotiated TLS version, for example `TLSv1.3` |
| `cipher` | TEXT | negotiated cipher suite |
| `kx_group` | TEXT | negotiated key-exchange group |
| `cert_alg` | TEXT | certificate public-key algorithm |
| `key_size` | INTEGER | certificate key size in bits |
| `sig_alg` | TEXT | certificate signature algorithm |
| `cert_expiry` | TEXT | certificate expiry date |
| `hybrid_flag` | INTEGER | 1 when the key exchange mixes post-quantum and classical |
| `status` | TEXT | `ok` or `error` |
| `error` | TEXT | failure message when `status = 'error'`, otherwise NULL |

The natural key is `(run_id, host, port)`. Re-scanning the same host in the
same run uses `ON CONFLICT (run_id, host, port) DO UPDATE`, so the existing row
is refreshed instead of being silently ignored or duplicated.

Rows with `status = 'error'` are kept on purpose. They record which hosts could
not be reached and why, which is part of the E2 result: a failed host is a
finding about coverage, not a reason to lose the row.

## `scores`

One row per finding **per planning scenario**. A finding can have several
scores because the Mosca verdict depends on the assumed shelf life, migration
time and quantum horizon.

| column | type | meaning |
|---|---|---|
| `finding_id` | INTEGER | foreign key to `findings.id` |
| `scenario` | TEXT | scenario key, for example `x15_y3_z15` |
| `shelf_life_years` | INTEGER | how long the data must stay secret |
| `migration_years` | INTEGER | assumed time to migrate |
| `quantum_years` | INTEGER | assumed time until a quantum computer |
| `alg_class` | TEXT | `hybrid`, `resistant`, `vulnerable`, `weakened` or `unknown` |
| `score_naive` | TEXT | baseline verdict with no timeline |
| `score_contextual` | TEXT | Mosca-based verdict |
| `reason` | TEXT | one-line explanation of the verdict |
| `migration_step` | TEXT | recommended next step |

The primary key is `(finding_id, scenario)`. Scores are deleted automatically
when their finding is deleted (`ON DELETE CASCADE`).

## `bench`

One row per measured operation, plus one row per measured size. E3 and E5
share this table; `constrained` says which run it came from.

| column | type | meaning |
|---|---|---|
| `id` | INTEGER | primary key |
| `run_id` | TEXT | `e3-bench` or `e5-bench` |
| `algo` | TEXT | algorithm label, for example `ML-KEM-768` |
| `op` | TEXT | operation or field, for example `encaps` or `ciphertext` |
| `ops_per_s` | REAL | operations per second (NULL for a size row) |
| `mean_ms` | REAL | milliseconds per operation (NULL for a size row) |
| `bytes` | INTEGER | size in bytes (NULL for a timing row) |
| `constrained` | INTEGER | 1 for the E5 constrained run, 0 for E3 |
| `ts` | TEXT | UTC timestamp of the measurement |

## Why two tables instead of one

The original design used a single `reason` column for two different things: why
a scan failed, and why a host scored high. Those are different facts with
different lifetimes. Splitting `findings` (scan facts) from `scores` (verdicts
per scenario) keeps each row honest and lets one finding carry many verdicts.
````

## 6. Create `tests/test_schema_docs.py`

Create the file with exactly this content:

```python
"""The schema document must stay in step with the real database.

If a column is added to ``scanner/db.py`` but not to ``scanner/SCHEMA.md``,
this test fails. That keeps the documentation honest instead of letting it
drift away from the code.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scanner.db import init_db

SCHEMA_DOC = Path("scanner/SCHEMA.md")
TABLES = ("findings", "scores", "bench")


def test_schema_doc_exists():
    assert SCHEMA_DOC.is_file(), "scanner/SCHEMA.md is missing"


@pytest.mark.parametrize("table", TABLES)
def test_every_column_is_documented(table, db_path):
    doc = SCHEMA_DOC.read_text(encoding="utf-8")
    assert f"`{table}`" in doc, f"table {table!r} is not in SCHEMA.md"

    conn = init_db(db_path)
    columns = [row["name"] for row in conn.execute(f"PRAGMA table_info({table})")]
    conn.close()

    assert columns, f"table {table!r} does not exist in the database"
    missing = [column for column in columns if f"`{column}`" not in doc]
    assert not missing, f"{table}: undocumented columns {missing}"


def test_upsert_key_and_error_rows_are_documented():
    doc = SCHEMA_DOC.read_text(encoding="utf-8")
    assert "ON CONFLICT (run_id, host, port)" in doc
    assert "error" in doc.lower()
```

## 7. Run the tests

Run only the new file first:

```bash
docker compose run --rm tools python -m pytest tests/test_schema_docs.py -q
```

Expected: `5 passed`.

Then run the whole suite:

```bash
docker compose run --rm tools python -m pytest tests -q
```

Expected: everything passes. The exact number will be 61 plus your new tests.
Do not change existing tests to make this pass.

## 8. Commit under your name

```bash
git config --local user.name  "Mohamad Talha Ezzo"
git config --local user.email "talhaezzo2006@gmail.com"

git checkout -b talha/schema-docs
git add scanner/SCHEMA.md tests/test_schema_docs.py
git status --short          # you should see only those two files
git commit -m "docs(scanner): document the findings, scores and bench schema"
```

If the branch already exists, use `git checkout talha/schema-docs` instead of
`git checkout -b`.

Copy the short commit hash:

```bash
git log --oneline -1
```

## 9. Record the contribution

Open `TeamWorkings/Mohamad_Talha_Ezzo/TASKS.md` and replace the empty row in
the **Contribution log** with:

```markdown
| 2026-11-03 | <short-hash> | T5 | Added scanner/SCHEMA.md and a test that keeps it in step with db.py | <NN> passed |
```

Use the hash from the previous step and the real test count. Then commit the
log entry:

```bash
git add TeamWorkings/Mohamad_Talha_Ezzo/TASKS.md
git commit -m "docs(team): record T5 in the contribution log"
git push -u origin talha/schema-docs
```

## 10. Rules

- Do not run `git add .` — it would stage another member's work.
- Do not invent results or numbers. This task changes a document and a test.
- Do not edit `scanner/db.py` in this task. The point is to document what is
  already there, not to change it.
- If a test fails, stop and show the output. Do not weaken the test.

## 11. Done checklist

- [ ] `scanner/SCHEMA.md` exists and describes all three tables.
- [ ] `tests/test_schema_docs.py` exists and passes.
- [ ] The full suite passes.
- [ ] The commit is authored by `Mohamad Talha Ezzo <talhaezzo2006@gmail.com>`.
- [ ] `TASKS.md` has a contribution-log row with the commit hash.
- [ ] The branch is pushed.
