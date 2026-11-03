# Bahaa Mohamad — Risk Analytics and Scoring

**Student ID:** 23001498
**Owned paths:** `scoring/`, `tests/test_rules.py`, `tests/test_mosca.py`
**Live module:** `scoring/` at the repository root.

This file is your work queue and contribution log. Pick a task, implement it in
the live module, add tests, commit under your own Git identity, and record the
commit below.

> **Start here:** [`HANDOFF.md`](HANDOFF.md) is a ready-to-paste 30-minute task
> for an AI coding agent. It contains the exact change, the test and the
> commands. This file stays the long-term queue.

---

## Tasks

| ID | Task | Acceptance criteria | Status |
|---|---|---|---|
| B1 | **Validate planning inputs.** Reject impossible scenarios with a clear `ValueError`: shelf life ≤ 0, horizon ≤ 0, migration < 0, or migration ≥ horizon. | `scenario_name`, `score` and `build_table` raise on bad input; valid calls are unchanged; tests cover each rejection. | ☐ |
| B2 | **Pin the score boundaries.** Add tests for `X == safe_window` (low), `X == safe_window + 3` (medium) and `X == safe_window + 4` (high), plus the hybrid/resistant/unknown paths. | Boundary tests in `tests/test_mosca.py`; no change to existing expected values. | ☐ |
| B3 | **Add a counterfactual explainer.** A function that answers "what would make this host low risk?" and returns a structured explanation plus a one-line sentence. | New `scoring/explain.py` with `explain(record, shelf_life_years, migration_years, quantum_years) -> dict`; tests assert the counterfactual threshold is correct for a high-risk host. | ☐ |
| B4 | **Prove the model is monotonic.** Increasing shelf life must never lower risk; increasing the quantum horizon must never raise it. | A deterministic sweep over the existing grid in `tests/test_mosca.py` asserts both properties for every algorithm class. | ☐ |
| B5 | **Document the model.** Add `scoring/README.md` with the class table, the Mosca formula, the boundary rules and two worked examples. | The document matches `scoring/mosca.py` and `scoring/rules.py`; a reader can reproduce the examples from the commands shown. | ☐ |

---

## Contribution log

| Date | Commit | Task | What changed | Tests |
|---|---|---|---|---|
| | | | | |

---

## Commit workflow

```bash
git config --local user.name  "Bahaa Mohamad"
git config --local user.email "your-github-email@example.com"

git checkout -b bahaa/scoring-validation
# implement B1 in scoring/ and tests/
docker compose run --rm tools python -m pytest tests -q
git add scoring tests/test_mosca.py tests/test_rules.py
git commit -m "feat(scoring): validate planning inputs"
git push -u origin bahaa/scoring-validation
```

Then update this file with the commit hash and open a pull request.

## Definition of done

- [ ] Code lives in the live module, not a copy.
- [ ] At least one new or updated test covers the change.
- [ ] `docker compose run --rm tools python -m pytest tests -q` passes.
- [ ] `scoring/README.md` is updated when rules or thresholds change.
- [ ] No generated data, certificates, logs or charts are committed.
- [ ] The contribution log above has a row for the commit.
