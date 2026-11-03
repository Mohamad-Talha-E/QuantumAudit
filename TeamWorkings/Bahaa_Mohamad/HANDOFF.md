# HANDOFF — Bahaa Mohamad

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

**Member:** Bahaa Mohamad (23001498)
**Area:** Risk Analytics and Scoring
**Git identity:** `Bahaa Mohamad <your-github-email@example.com>`
**Branch:** `bahaa/scoring-validation`
**Task:** B1 — Validate planning inputs
**Time budget:** about 30 minutes

> **Before you start:** replace the email above with the email linked to your
> GitHub account, and run:
>
> ```bash
> git config --local user.name  "Bahaa Mohamad"
> git config --local user.email "your-github-email@example.com"
> ```
>
> If the email stays as `your-github-email@example.com`, the commit will not
> appear on your GitHub profile.

---

## 1. What QuantumAudit is

QuantumAudit scans TLS servers, records which cryptography they use, and scores
the risk that a future quantum computer breaks it. Your module is the scorer:
it turns raw scan facts into a low / medium / high verdict using Mosca's
inequality.

## 2. What you own

You own `scoring/` and its tests. For this task you will touch only:

- `scoring/mosca.py`
- `scoring/sensitivity.py`
- `tests/test_mosca.py`
- `TeamWorkings/Bahaa_Mohamad/TASKS.md` — to record the commit

Do **not** edit `scanner/`, `lab/`, `dashboard/` or another member's files.

## 3. The task in plain language

The scorer accepts three planning numbers: shelf life, migration time and
quantum horizon. Some combinations make no sense: a shelf life of zero, a
negative migration time, or a migration that takes longer than the time until
the quantum computer arrives. Right now the code silently accepts them and
produces a meaningless verdict.

Add a `validate_planning` function that rejects bad inputs with a clear
`ValueError`, call it from the scoring functions, and add tests for every
rejection.

## 4. Read these first

- `scoring/mosca.py` — the constants, `scenario_name` and `score`.
- `scoring/sensitivity.py` — `build_table`, the E6 grid.
- `tests/test_mosca.py` — the existing tests and the `VULNERABLE` fixture.

## 5. Edit `scoring/mosca.py`

### 5.1 Add `validate_planning` before `scenario_name`

Find this:

```python
def scenario_name(shelf_life: int, migration: int, horizon: int) -> str:
    """Stable key for a planning scenario, e.g. ``x15_y3_z15``."""
    return f"x{shelf_life}_y{migration}_z{horizon}"
```

Replace it with this:

```python
def validate_planning(
    shelf_life_years: int, migration_years: int, quantum_years: int
) -> None:
    """Reject planning inputs that cannot describe a real scenario.

    Raises ``ValueError`` with a message a user can act on. A negative or zero
    time horizon makes the Mosca inequality meaningless, and a migration time
    longer than the horizon means there is no safe window at all.
    """
    if shelf_life_years <= 0:
        raise ValueError("shelf life must be greater than 0 years")
    if quantum_years <= 0:
        raise ValueError("quantum horizon must be greater than 0 years")
    if migration_years < 0:
        raise ValueError("migration time cannot be negative")
    if migration_years >= quantum_years:
        raise ValueError("migration time must be shorter than the quantum horizon")


def scenario_name(shelf_life: int, migration: int, horizon: int) -> str:
    """Stable key for a planning scenario, e.g. ``x15_y3_z15``."""
    validate_planning(shelf_life, migration, horizon)
    return f"x{shelf_life}_y{migration}_z{horizon}"
```

### 5.2 Call it from `score`

Find this:

```python
    """Return ``(level, reason, migration_step)`` for one scanned host."""
    alg_class = classify(record)
```

Replace it with this:

```python
    """Return ``(level, reason, migration_step)`` for one scanned host."""
    validate_planning(shelf_life_years, migration_years, quantum_years)
    alg_class = classify(record)
```

## 6. Edit `scoring/sensitivity.py`

### 6.1 Import the validator

Find this:

```python
from scoring.mosca import HORIZONS, MIGRATION_STEP, SHELF_LIVES, naive_score, score
```

Replace it with this:

```python
from scoring.mosca import (
    HORIZONS,
    MIGRATION_STEP,
    SHELF_LIVES,
    naive_score,
    score,
    validate_planning,
)
```

### 6.2 Validate the E6 grid

Find this:

```python
    """Return per-scenario distributions plus flip counts."""
    conn = init_db(db)
```

Replace it with this:

```python
    """Return per-scenario distributions plus flip counts."""
    if not shelf_lives or not horizons:
        raise ValueError("shelf_lives and horizons must not be empty")
    for shelf in shelf_lives:
        for horizon in horizons:
            validate_planning(shelf, migration_years, horizon)

    conn = init_db(db)
```

## 7. Edit `tests/test_mosca.py`

### 7.1 Update the imports

Find this:

```python
from scoring.mosca import naive_score, safe_window, scenario_name, score
```

Replace it with this:

```python
from scoring.mosca import (
    naive_score,
    safe_window,
    scenario_name,
    score,
    validate_planning,
)
from scoring.sensitivity import build_table
```

### 7.2 Append the new tests

Add this to the end of the file:

```python
@pytest.mark.parametrize(
    "shelf, migration, horizon",
    [
        (0, 3, 15),     # shelf life must be positive
        (-1, 3, 15),    # negative shelf life
        (15, -1, 15),   # migration cannot be negative
        (15, 15, 15),   # migration equal to the horizon
        (15, 16, 15),   # migration beyond the horizon
        (15, 3, 0),     # horizon must be positive
    ],
)
def test_validate_planning_rejects_impossible_scenarios(shelf, migration, horizon):
    with pytest.raises(ValueError):
        validate_planning(shelf, migration, horizon)


def test_valid_planning_is_accepted():
    validate_planning(15, 3, 15)  # must not raise


def test_scenario_name_rejects_impossible_scenario():
    with pytest.raises(ValueError):
        scenario_name(15, 3, 3)


def test_score_rejects_impossible_scenario():
    with pytest.raises(ValueError):
        score(VULNERABLE, shelf_life_years=0)


def test_build_table_rejects_migration_beyond_horizon(db_path):
    with pytest.raises(ValueError):
        build_table("any-run", db=db_path, horizons=(10,), migration_years=10)
```

## 8. Run the tests

Run only your file first:

```bash
docker compose run --rm tools python -m pytest tests/test_mosca.py -q
```

Expected: `20 passed` (10 old + 10 new).

Then the whole suite:

```bash
docker compose run --rm tools python -m pytest tests -q
```

Expected: everything passes. Do not change existing expected values.

## 9. Commit under your name

```bash
git checkout -b bahaa/scoring-validation
git add scoring/mosca.py scoring/sensitivity.py tests/test_mosca.py
git status --short          # you should see only those three files
git commit -m "feat(scoring): validate planning inputs"
```

If the branch already exists, use `git checkout bahaa/scoring-validation`
instead of `git checkout -b`.

Copy the short commit hash:

```bash
git log --oneline -1
```

## 10. Record the contribution

Open `TeamWorkings/Bahaa_Mohamad/TASKS.md` and replace the empty row in the
**Contribution log** with:

```markdown
| 2026-11-03 | <short-hash> | B1 | Added validate_planning and rejection tests | <NN> passed |
```

Use the hash from the previous step and the real test count. Then:

```bash
git add TeamWorkings/Bahaa_Mohamad/TASKS.md
git commit -m "docs(team): record B1 in the contribution log"
git push -u origin bahaa/scoring-validation
```

## 11. Rules

- Do not run `git add .` — it would stage another member's work.
- Do not change the default scenario or any existing expected value.
- Do not invent results. This task adds validation and tests only.
- If a test fails, stop and show the output. Do not weaken the test.

## 12. Done checklist

- [ ] `validate_planning` exists and raises `ValueError` for each bad input.
- [ ] `scenario_name`, `score` and `build_table` all use it.
- [ ] The new tests pass and the old tests still pass.
- [ ] The commit is authored by `Bahaa Mohamad` with your GitHub email.
- [ ] `TASKS.md` has a contribution-log row with the commit hash.
- [ ] The branch is pushed.
