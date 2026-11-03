# HANDOFF — Ahmad Abualrub

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

**Member:** Ahmad Abualrub (23001599)
**Area:** Lab and Cryptographic Benchmarking
**Git identity:** `Ahmad Abualrub <your-github-email@example.com>`
**Branch:** `ahmad/bench-variance`
**Task:** A1 — Add a benchmark summary helper
**Time budget:** about 30 minutes

> **Before you start:** replace the email above with the email linked to your
> GitHub account, and run:
>
> ```bash
> git config --local user.name  "Ahmad Abualrub"
> git config --local user.email "your-github-email@example.com"
> ```
>
> If the email stays as `your-github-email@example.com`, the commit will not
> appear on your GitHub profile.

---

## 1. What QuantumAudit is

QuantumAudit scans TLS servers, records which cryptography they use, and scores
the risk that a future quantum computer breaks it. Your module is the lab and
the benchmark harness. It measures how fast classical and post-quantum
algorithms run (E3), how much overhead a hybrid handshake adds (E4), and how
they behave on a small, constrained machine (E5).

## 2. What you own

You own `lab/` and the toolbox image. For this task you will touch only:

- `lab/bench.py`
- `tests/test_lab_bench.py` — **new file**
- `TeamWorkings/Ahmad_Abualrub/TASKS.md` — to record the commit

Do **not** edit `scanner/`, `scoring/`, `dashboard/` or another member's files.

## 3. The task in plain language

A single benchmark run gives one number per operation. One number cannot tell
you whether the result is stable or noisy. Add a small pure function,
`summarise(samples)`, that turns a list of repeated measurements into a count,
mean, standard deviation, minimum and maximum. It must handle one sample and an
empty list without crashing.

This is the first half of task A1. Wiring the new columns into the Markdown
report is A1b and can be your next task.

## 4. Read these first

- `lab/bench.py` — `SPECS`, `parse_rates`, `to_markdown`, `main`.
- `tests/test_kx.py` — the style used by the existing tests.

## 5. Edit `lab/bench.py`

### 5.1 Add the `statistics` import

Find this:

```python
import argparse
import datetime as dt
import os
import re
import subprocess
import tempfile
```

Replace it with this:

```python
import argparse
import datetime as dt
import os
import re
import statistics
import subprocess
import tempfile
```

### 5.2 Add `summarise` before `_run`

Find this:

```python
def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, **kwargs)
```

Replace it with this:

```python
def summarise(samples: list[float]) -> dict:
    """Summarise repeated measurements of one operation.

    Returns the count, mean, sample standard deviation, minimum and maximum.
    A single sample has zero spread. An empty list returns ``None`` for every
    statistic instead of raising, so a missing measurement is visible in the
    report rather than crashing the benchmark.
    """
    if not samples:
        return {
            "count": 0,
            "mean": None,
            "stdev": None,
            "min": None,
            "max": None,
        }
    return {
        "count": len(samples),
        "mean": statistics.fmean(samples),
        "stdev": statistics.stdev(samples) if len(samples) > 1 else 0.0,
        "min": min(samples),
        "max": max(samples),
    }


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, **kwargs)
```

## 6. Create `tests/test_lab_bench.py`

Create the file with exactly this content:

```python
"""Tests for the benchmark summary helper.

``summarise`` is pure: it takes a list of numbers and returns statistics, so it
can be tested without running OpenSSL or starting the lab.
"""

from __future__ import annotations

import pytest

from lab.bench import summarise


def test_summarise_three_samples():
    result = summarise([10.0, 20.0, 30.0])
    assert result["count"] == 3
    assert result["mean"] == 20.0
    assert result["stdev"] == pytest.approx(10.0)
    assert result["min"] == 10.0
    assert result["max"] == 30.0


def test_summarise_single_sample_has_zero_spread():
    result = summarise([5.0])
    assert result["count"] == 1
    assert result["mean"] == 5.0
    assert result["stdev"] == 0.0


def test_summarise_empty_is_none_not_an_error():
    result = summarise([])
    assert result["count"] == 0
    assert result["mean"] is None
    assert result["stdev"] is None
    assert result["min"] is None
    assert result["max"] is None
```

## 7. Run the tests

Run only your file first:

```bash
docker compose run --rm tools python -m pytest tests/test_lab_bench.py -q
```

Expected: `3 passed`.

Then the whole suite:

```bash
docker compose run --rm tools python -m pytest tests -q
```

Expected: everything passes. This task does **not** need the lab container or
OpenSSL, because `summarise` is pure arithmetic.

## 8. Commit under your name

```bash
git checkout -b ahmad/bench-variance
git add lab/bench.py tests/test_lab_bench.py
git status --short          # you should see only those two files
git commit -m "feat(lab): add benchmark summary helper"
```

If the branch already exists, use `git checkout ahmad/bench-variance` instead
of `git checkout -b`.

Copy the short commit hash:

```bash
git log --oneline -1
```

## 9. Record the contribution

Open `TeamWorkings/Ahmad_Abualrub/TASKS.md` and replace the empty row in the
**Contribution log** with:

```markdown
| 2026-11-03 | <short-hash> | A1 | Added summarise() for benchmark variance and its tests | <NN> passed |
```

Use the hash from the previous step and the real test count. Then:

```bash
git add TeamWorkings/Ahmad_Abualrub/TASKS.md
git commit -m "docs(team): record A1 in the contribution log"
git push -u origin ahmad/bench-variance
```

## 10. Rules

- Do not run `git add .` — it would stage another member's work.
- Do not run a real benchmark for this task. It needs no OpenSSL.
- Do not invent timing numbers. This task adds a helper and tests only.
- If a test fails, stop and show the output. Do not weaken the test.

## 11. Done checklist

- [ ] `summarise` exists in `lab/bench.py`.
- [ ] It handles three samples, one sample and an empty list.
- [ ] `tests/test_lab_bench.py` passes.
- [ ] The full suite passes.
- [ ] The commit is authored by `Ahmad Abualrub` with your GitHub email.
- [ ] `TASKS.md` has a contribution-log row with the commit hash.
- [ ] The branch is pushed.
