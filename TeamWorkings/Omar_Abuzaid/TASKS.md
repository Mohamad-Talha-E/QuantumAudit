# Omar Abuzaid — Dashboard and Documentation

**Student ID:** 23001809
**Owned paths:** `dashboard/`, `tests/test_dashboard.py`, `README.md`,
`REPORT.md`, `results.md`, `DEVIATIONS.md`
**Live module:** `dashboard/` at the repository root.

This file is your work queue and contribution log. Pick a task, implement it in
the live module, add tests, commit under your own Git identity, and record the
commit below.

---

## Tasks

| ID | Task | Acceptance criteria | Status |
|---|---|---|---|
| O1 | **Filter and paginate the findings table.** Add a text filter and page controls to the dashboard, backed by a `q` parameter on `/api/findings`. | Filtering by host or algorithm returns only matching rows; pagination returns stable pages; tests cover `q`, `limit` and `offset`. | ☐ |
| O2 | **Add a methodology page.** A `/methodology` page that states the Mosca formula, the class rules, the scenario defaults and the limitations. | Returns 200; contains the formula and the default scenario; a test checks the rendered text. | ☐ |
| O3 | **Accessibility pass.** Add a table caption, explicit form labels, visible focus styles, and badges that do not rely on colour alone. | Manual checklist in the PR; no visual regression in the existing pages. | ☐ |
| O4 | **Broaden the API tests.** Cover `/api/findings` pagination, `/api/sensitivity` shape, and a 404 for an unknown run on every endpoint. | New tests in `tests/test_dashboard.py`; all pass. | ☐ |
| O5 | **Add a reproducibility appendix.** Extend `REPORT.md` and `results.md` with the exact environment, commands and a note on how to regenerate every table. | Every result table in the report has a command that regenerates it; `README.md` links to the appendix. | ☐ |

---

## Contribution log

| Date | Commit | Task | What changed | Tests |
|---|---|---|---|---|
| | | | | |

---

## Commit workflow

```bash
git config --local user.name  "Omar Abuzaid"
git config --local user.email "your-github-email@example.com"

git checkout -b omar/dashboard-filter
# implement O1 in dashboard/ and tests/
docker compose run --rm tools python -m pytest tests -q
git add dashboard tests/test_dashboard.py
git commit -m "feat(dashboard): add findings filter and pagination"
git push -u origin omar/dashboard-filter
```

Then update this file with the commit hash and open a pull request.

## Definition of done

- [ ] Code lives in the live module, not a copy.
- [ ] At least one new or updated test covers the change.
- [ ] `docker compose run --rm tools python -m pytest tests -q` passes.
- [ ] The dashboard still loads at `http://localhost:8000`.
- [ ] Documentation is updated when behaviour or numbers change.
- [ ] No generated charts, databases or CSVs are committed.
- [ ] The contribution log above has a row for the commit.
