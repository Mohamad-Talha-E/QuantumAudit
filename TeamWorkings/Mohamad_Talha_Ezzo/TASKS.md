# Mohamad Talha Ezzo — Scanner and Data Engineering

**Student ID:** 23000488
**Owned paths:** `scanner/`, `tests/conftest.py`, `tests/test_db.py`,
`tests/test_kx.py`, `tests/test_scan.py`, `docker-compose.yml`,
`requirements.txt`, `.dockerignore`, `.gitignore`
**Live module:** `scanner/` at the repository root.

This file is your work queue and contribution log. Pick a task, implement it in
the live module, add tests, commit under your own Git identity, and record the
commit below.

---

## Tasks

| ID | Task | Acceptance criteria | Status |
|---|---|---|---|
| T1 | **Add a `scan-diff` command.** Compare two runs and report hosts that were added, removed, or changed (protocol, key exchange, certificate algorithm, hybrid flag). | `python -m scanner.cli diff --run-a e1-lab --run-b e1-lab-2` prints three sections; exits 0 even when there are no differences; tests in `tests/test_diff.py`. | ☐ |
| T2 | **Add retry with backoff for transient failures.** Retry DNS/timeout errors up to 2 extra times with a short, jittered delay. Keep permanent TLS errors non-retried. | A host that times out twice then succeeds is recorded `ok`; a host that always times out is recorded `error` with the attempt count; unit tests use a fake scanner function. | ☐ |
| T3 | **Add an export command.** Write one run to CSV or JSON for analysis outside SQLite. | `python -m scanner.cli export --run-id e2-tranco --format csv` writes `data/exports/e2-tranco.csv`; `--format json` writes the same rows as JSON; tests check headers and row counts. | ☐ |
| T4 | **Harden target parsing and document the scanner.** Cover bracketed IPv6, bare IPv6, hostnames with trailing dots, and SNI behaviour for IP literals. Add `scanner/README.md`. | New parametrised cases in `tests/test_scan.py`; SNI is not sent for IP literals; `scanner/README.md` documents every subcommand and the error categories. | ☐ |
| T5 | **Document the data model.** Add a short `scanner/SCHEMA.md` describing `findings`, `scores` and `bench`, including the upsert key and why error rows are kept. | The document matches `scanner/db.py`; a test asserts the documented table and column names exist. | ☐ |

---

## Contribution log

| Date | Commit | Task | What changed | Tests |
|---|---|---|---|---|
| | | | | |

---

## Commit workflow

```bash
git config --local user.name  "Mohamad Talha Ezzo"
git config --local user.email "talhaezzo2006@gmail.com"

git checkout -b talha/scanner-diff
# implement T1 in scanner/ and tests/
docker compose run --rm tools python -m pytest tests -q
git add scanner tests
git commit -m "feat(scanner): add scan-diff command for two-run comparison"
git push -u origin talha/scanner-diff
```

Then update this file with the commit hash and open a pull request.

## Definition of done

- [ ] Code lives in the live module, not a copy.
- [ ] At least one new or updated test covers the change.
- [ ] `docker compose run --rm tools python -m pytest tests -q` passes.
- [ ] `scanner/README.md` or `scanner/SCHEMA.md` is updated when behaviour changes.
- [ ] No generated data, certificates, logs or charts are committed.
- [ ] The contribution log above has a row for the commit.
