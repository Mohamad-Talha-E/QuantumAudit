# HANDOFF — Omar Abuzaid

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

**Member:** Omar Abuzaid (23001809)
**Area:** Dashboard and Documentation
**Git identity:** `Omar Abuzaid <your-github-email@example.com>`
**Branch:** `omar/findings-filter`
**Task:** O1 — Add a text filter to the findings API
**Time budget:** about 30 minutes

> **Before you start:** replace the email above with the email linked to your
> GitHub account, and run:
>
> ```bash
> git config --local user.name  "Omar Abuzaid"
> git config --local user.email "your-github-email@example.com"
> ```
>
> If the email stays as `your-github-email@example.com`, the commit will not
> appear on your GitHub profile.

---

## 1. What QuantumAudit is

QuantumAudit scans TLS servers, records which cryptography they use, and scores
the risk that a future quantum computer breaks it. Your module is the
dashboard: it reads the database and shows the scan results, the risk verdicts
and the sensitivity analysis in a browser.

## 2. What you own

You own `dashboard/` and its tests. For this task you will touch only:

- `dashboard/app.py`
- `tests/test_dashboard.py`
- `TeamWorkings/Omar_Abuzaid/TASKS.md` — to record the commit

Do **not** edit `scanner/`, `scoring/`, `lab/` or another member's files.

## 3. The task in plain language

The findings table can show hundreds of rows. Add a text filter so a user can
ask for one host or one algorithm. The filter goes through the API as a `q`
parameter and matches the host, key-exchange group, certificate algorithm or
cipher. It must be case-insensitive and it must not be possible to inject SQL.

This is the backend half of task O1. Adding the search box and page buttons to
the HTML is O1b and can be your next task.

## 4. Read these first

- `dashboard/app.py` — `run_findings` and `api_findings`.
- `tests/test_dashboard.py` — the `seeded` fixture and the existing tests.

## 5. Edit `dashboard/app.py`

### 5.1 Replace `run_findings`

Find this whole function:

```python
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
```

Replace it with this:

```python
def run_findings(
    run_id: str,
    scenario: str,
    limit: int,
    offset: int,
    q: str | None = None,
) -> list[dict]:
    """Return one page of findings, optionally filtered by a text query.

    ``q`` is matched case-insensitively against the host, key-exchange group,
    certificate algorithm and cipher. It is always passed as a SQL parameter,
    never interpolated, so the query text cannot be injected.
    """
    conn = _connect()
    where = "f.run_id = ?"
    params: list = [scenario, run_id]
    if q:
        where += (
            " AND (f.host LIKE ? OR f.kx_group LIKE ?"
            " OR f.cert_alg LIKE ? OR f.cipher LIKE ?)"
        )
        like = f"%{q}%"
        params.extend([like, like, like, like])
    params.extend([limit, offset])

    rows = conn.execute(
        f"""
        SELECT f.host, f.port, f.protocol, f.cipher, f.kx_group, f.cert_alg,
               f.key_size, f.hybrid_flag, f.status, f.error,
               s.alg_class, s.score_contextual, s.score_naive,
               s.reason, s.migration_step
        FROM findings f
        LEFT JOIN scores s
               ON s.finding_id = f.id AND s.scenario = ?
        WHERE {where}
        ORDER BY
            CASE s.score_contextual
                WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END,
            f.host
        LIMIT ? OFFSET ?
        """,
        params,
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
```

### 5.2 Replace `api_findings`

Find this:

```python
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
```

Replace it with this:

```python
@app.get("/api/findings")
def api_findings(
    run_id: str,
    scenario: str = Query(DEFAULT_SCENARIO),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    q: str | None = Query(None, description="Case-insensitive text filter"),
) -> dict:
    return {
        "run_id": run_id,
        "scenario": scenario,
        "limit": limit,
        "offset": offset,
        "q": q,
        "findings": run_findings(run_id, scenario, limit, offset, q),
    }
```

## 6. Edit `tests/test_dashboard.py`

Add this to the end of the file:

```python
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
```

## 7. Run the tests

Run only your file first:

```bash
docker compose run --rm tools python -m pytest tests/test_dashboard.py -q
```

Expected: `11 passed` (6 old + 5 new).

Then the whole suite:

```bash
docker compose run --rm tools python -m pytest tests -q
```

Expected: everything passes.

## 8. Commit under your name

```bash
git checkout -b omar/findings-filter
git add dashboard/app.py tests/test_dashboard.py
git status --short          # you should see only those two files
git commit -m "feat(dashboard): add text filter to findings API"
```

If the branch already exists, use `git checkout omar/findings-filter` instead
of `git checkout -b`.

Copy the short commit hash:

```bash
git log --oneline -1
```

## 9. Record the contribution

Open `TeamWorkings/Omar_Abuzaid/TASKS.md` and replace the empty row in the
**Contribution log** with:

```markdown
| 2026-11-03 | <short-hash> | O1 | Added q filter to findings API with pagination tests | <NN> passed |
```

Use the hash from the previous step and the real test count. Then:

```bash
git add TeamWorkings/Omar_Abuzaid/TASKS.md
git commit -m "docs(team): record O1 in the contribution log"
git push -u origin omar/findings-filter
```

## 10. Rules

- Do not run `git add .` — it would stage another member's work.
- Never build SQL by pasting `q` into the string. It must stay a `?` parameter.
- Do not change the default scenario or the sort order.
- Do not invent results. This task changes the API and its tests only.
- If a test fails, stop and show the output. Do not weaken the test.

## 11. Done checklist

- [ ] `/api/findings` accepts `q` and returns it in the response.
- [ ] Filtering matches host, key exchange, certificate and cipher.
- [ ] Filtering is case-insensitive.
- [ ] The new tests pass and the old tests still pass.
- [ ] The commit is authored by `Omar Abuzaid` with your GitHub email.
- [ ] `TASKS.md` has a contribution-log row with the commit hash.
- [ ] The branch is pushed.
