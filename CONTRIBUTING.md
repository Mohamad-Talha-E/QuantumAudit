# Contributing to QuantumAudit

This repository is a four-person course project. Each member owns one module and
contributes real changes to it. This document is the workflow everyone follows.

---

## 1. Who owns what

| Member | Module | Paths |
|---|---|---|
| Mohamad Talha Ezzo | Scanner and Data Engineering | `scanner/`, scanner tests, compose and requirements |
| Bahaa Mohamad | Risk Analytics and Scoring | `scoring/`, `tests/test_rules.py`, `tests/test_mosca.py` |
| Ahmad Abualrub | Lab and Cryptographic Benchmarking | `lab/`, `docker/tools/` |
| Omar Abuzaid | Dashboard and Documentation | `dashboard/`, `tests/test_dashboard.py`, `README.md`, `REPORT.md`, `results.md`, `DEVIATIONS.md` |

The full path map is in [`TeamWorkings/OWNERSHIP.md`](TeamWorkings/OWNERSHIP.md).
Each member's task queue is in `TeamWorkings/<Name>/TASKS.md`.

---

## 2. One-time setup

```bash
git clone https://github.com/Mohamad-Talha-E/QuantumAudit.git
cd QuantumAudit
git checkout build/full-system
git pull origin build/full-system
```

Set **your own** identity. Use the email linked to your GitHub account, or the
commit will not appear on your profile.

```bash
git config --local user.name  "Your Full Name"
git config --local user.email "your-github-email@example.com"
```

Verify:

```bash
git config --local user.name
git config --local user.email
```

Everything runs in Docker, so no local OpenSSL or Python packages are needed:

```bash
docker compose build
docker compose run --rm tools python -m pytest tests -q
```

---

## 3. Workflow

### Step 1 — Pick a task

Open your `TeamWorkings/<Name>/TASKS.md`, choose a task, and note its ID.

### Step 2 — Create a branch

Name the branch after yourself and the task:

```bash
git checkout -b bahaa/scoring-validation
```

Prefixes: `talha/`, `bahaa/`, `ahmad/`, `omar/`.

### Step 3 — Implement in the live module

Change the real module, not a copy. Add or update a test that would fail without
your change. If the change affects another module, follow the cross-module
protocol in `TeamWorkings/OWNERSHIP.md` §3.

### Step 4 — Run the suite

```bash
docker compose run --rm tools python -m pytest tests -q
```

If your change touches the lab, also confirm the lab still starts:

```bash
docker compose up -d lab
docker compose run --rm tools python -m lab.evaluate
```

If your change touches the dashboard:

```bash
docker compose up -d dashboard
# open http://localhost:8000
```

### Step 5 — Commit

Use a clear, scoped message:

```
feat(scanner): add scan-diff command for two-run comparison
fix(scoring): reject migration time greater than the quantum horizon
test(dashboard): cover findings pagination and unknown-run 404
docs(lab): document certificate regeneration and server layout
```

Format: `type(scope): summary`, where `type` is `feat`, `fix`, `test`, `docs`,
`refactor` or `chore`, and `scope` is the module.

```bash
git add scanner tests
git commit -m "feat(scanner): add scan-diff command for two-run comparison"
```

### Step 6 — Record it

Add a row to the **Contribution log** in your `TASKS.md`:

```markdown
| 2026-11-10 | a1b2c3d | T1 | Added scan-diff command and tests | 64 passed |
```

### Step 7 — Push and open a pull request

```bash
git push -u origin bahaa/scoring-validation
```

Open a pull request into `build/full-system`. Fill in the pull-request template.
Request a review from the owner of any other module you touched.

---

## 4. Definition of done

A change is done when all of these are true:

- [ ] The change is in the live module, not a copy.
- [ ] A test would fail without the change.
- [ ] `docker compose run --rm tools python -m pytest tests -q` passes.
- [ ] The module's `README.md` (or `REPORT.md` / `results.md`) is updated if
      behaviour or numbers changed.
- [ ] No generated data is committed (see §6).
- [ ] Your `TASKS.md` contribution log has a row for the commit.
- [ ] The pull request is approved by the required reviewer.

---

## 5. Review rules

- The owner of a touched module is the required reviewer.
- A reviewer checks: the change is real and in the right module, a test covers
  it, the suite passes, and no generated data is included.
- Cross-module changes need both owners to approve.
- Do not approve your own pull request.
- Reviews should happen within two working days.

`CODEOWNERS` requests the right reviewer automatically. Branch protection can
enforce the approval; see `TeamWorkings/OWNERSHIP.md` §5.

---

## 6. What not to commit

These are generated and already ignored by `.gitignore`:

- `data/*.db`, `data/*.csv`, `data/tranco/`
- `lab/certs/`, `lab/servers/`, `lab/logs/`
- `dashboard/static/charts/`
- `__pycache__/`, `.pytest_cache/`

They are reproducible from the commands in `results.md`. Committing them bloats
the repository and invites stale results.

---

## 7. Troubleshooting

### Push rejected (`non-fast-forward`)

Someone pushed before you:

```bash
git pull --rebase origin build/full-system
git push origin build/full-system
```

### Wrong author on your last commit (not pushed yet)

```bash
git commit --amend --reset-author --no-edit
```

### Wrong author on a commit that is already pushed

Do not rewrite shared history. Make a small follow-up commit with the correct
identity, or coordinate with the team before any rebase.

### You staged another module by accident

```bash
git restore --staged scoring
git status --short
```

### Your commit does not appear on your GitHub profile

The email in `git config user.email` is not linked to your account. Add it under
**Settings → Emails**, or amend before pushing.

### "Nothing to commit"

Your task may already be in progress on another branch. Check:

```bash
git log --oneline --all -- <path>
git branch --all
```

---

## 8. After all four members have contributed

```bash
git log --oneline --graph --decorate -20
git shortlog -sne
```

The shortlog should show each member with their own commits. Then open a pull
request from `build/full-system` into `main`, or merge after team review.
