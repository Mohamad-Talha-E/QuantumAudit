# NEXT_STEPS — resume here

This file is the project's memory. If a chat is lost, this file still says where
the work stands and what to do next.

**Last verified:** 2026-11-03
**Branch:** `build/full-system`
**Last commit:** `f3766d2` — `docs(team): add 30-minute per-member handoffs`
**Pushed:** yes, `origin/build/full-system`
**Tests:** `61 passed`
**`main`:** untouched. It has **not** been merged into yet.

Read this file first, then `TeamWorkings/README.md`.

---

## 0. Current state at a glance

| Area | State |
|---|---|
| Scanner (`scanner/`) | Working. E1 accuracy 100%. |
| Risk scorer (`scoring/`) | Working. Mosca + naive baseline. |
| Lab (`lab/`) | Working. 20 TLS servers, E1/E3/E4/E5. |
| Dashboard (`dashboard/`) | Working. FastAPI + server-side PNG charts. |
| Experiments E1–E6 | Done. Numbers in `results.md`. |
| Tests | 61 passing. |
| Documentation | `README.md`, `REPORT.md`, `results.md`, `DEVIATIONS.md`. |
| Team ownership | `TeamWorkings/`, `CODEOWNERS`, `CONTRIBUTING.md`. |
| Per-member handoffs | Written and dry-run together: **84 passed**. |
| Teammate commits | **None yet.** Each member must run their own handoff. |
| Merge to `main` | **Not done.** Deliberate. |
| Submission packaging | **Not done.** |

### What is finished and should not be redone

- All six experiments have real measured numbers. Do not invent or "improve" a
  number. If a re-run differs, record the new run and say why.
- The four `HANDOFF.md` files contain exact code, exact tests, exact commands
  and the commit steps. They were verified in a clean copy of the repository.
- The ownership model is real. Each member changes their own live module.

---

## 1. Resume in 60 seconds

### If the folder already exists

```bash
cd "C:\Users\Ziad Ezzo\Desktop\STICS\QuantumAudit"
git status
git checkout build/full-system
git pull origin build/full-system
git log --oneline -5
```

A clean `git status` means nothing was lost.

### If you are on a new machine

```bash
git clone https://github.com/Mohamad-Talha-E/QuantumAudit.git
cd QuantumAudit
git checkout build/full-system
```

### Then confirm the environment

```bash
docker --version
docker compose version
docker compose build tools
docker compose run --rm tools python -m pytest tests -q
```

Expected: `61 passed`.

Docker is required. Native Windows does not have OpenSSL 3.5, so ML-KEM and
ML-DSA commands fail outside the container. See `DEVIATIONS.md` §1.1.

---

## 2. What is in Git and what is not

### In Git

All code, tests, documentation, the lab scripts, the manifest and the
`TeamWorkings/` ownership files.

### Not in Git (on purpose)

These are reproducible outputs. They are listed in `.gitignore`.

- `data/*.db` — SQLite database
- `data/*.csv`, `data/tranco/` — downloaded Tranco list
- `data/*.md`, `data/*.json` — generated experiment reports
- `lab/certs/` — generated CA and certificates
- `lab/servers/` — generated server configs
- `lab/logs/` — server logs
- `dashboard/static/charts/` — generated PNG charts

**Consequence:** after a fresh clone the dashboard has no data. That is normal.
`results.md` is the source of truth for the measured numbers. To make the
dashboard show data again, rerun E1 and E2 (commands below).

**Do not commit generated data.** `DEVIATIONS.md` §8.3 explains why.

---

## 3. Reproduce the experiments (exact commands)

Run everything from the repository root. All Python runs inside the `tools`
container.

### E1 — Scanner accuracy against the lab

```bash
docker compose up -d lab
docker compose run --rm tools python -m lab.evaluate
```

Optional: store the scan in the database too.

```bash
docker compose run --rm tools python -m scanner.cli scan-lab \
    --run-id e1-lab --fresh
```

Expected: 20/20 exact match; precision = recall = 1.00.

### E2 — Public TLS survey (100-domain sample)

```bash
docker compose run --rm tools python -m scanner.cli scan-tranco \
    --n 100 --seed 413 --pool 10000 --run-id e2-tranco
docker compose run --rm tools python -m scanner.cli score \
    --run-id e2-tranco --all-scenarios
```

Expected: 73 reachable of 100; 44 hybrid; 29 classical-only.

The full 1,000-domain run is optional and documented in `DEVIATIONS.md` §5.2:

```bash
docker compose run --rm tools python -m scanner.cli scan-tranco \
    --n 1000 --seed 413 --pool 10000 --run-id e2-tranco-1000 --delay 0.5
```

### E3 — Classical vs post-quantum benchmark

```bash
docker compose run --rm tools python -m lab.bench --run-id e3-bench
```

### E4 — Hybrid handshake overhead

The lab must be running (ports 8443 and 8447).

```bash
docker compose up -d lab
docker compose run --rm tools python -m lab.e4_handshake \
    --host lab --cafile lab/certs/ca.pem
```

Expected: about +0.8% time, +80.9% bytes.

### E5 — Constrained benchmark (0.5 CPU, 256 MB)

```bash
docker run --rm --cpus=0.5 --memory=256m \
    -v "$PWD:/app" -w /app quantumaudit/tools:latest \
    python -m lab.bench --constrained --run-id e5-constrained
```

On PowerShell, replace `$PWD` with `${PWD}`.

### E6 — Sensitivity analysis

```bash
docker compose run --rm tools python -m scanner.cli sensitivity \
    --run-id e2-tranco
```

Writes `data/e6_report.md` and `data/e6_report.json`.

### Dashboard

```bash
docker compose up -d dashboard
# http://localhost:8000
```

### All tests

```bash
docker compose run --rm tools python -m pytest tests -q
```

### Stop the lab when finished

```bash
docker compose down
```

---

## 4. Teammate work — the next real milestone

Each member has a 30-minute task with exact code and tests. Each person must
run **their own** handoff and commit under **their own** Git identity. Do not
commit on their behalf; that would make the contribution history false.

| Member | Module | Handoff | Branch | Task |
|---|---|---|---|---|
| Mohamad Talha Ezzo | `scanner/` | `TeamWorkings/Mohamad_Talha_Ezzo/HANDOFF.md` | `talha/schema-docs` | T5 — schema docs + test |
| Bahaa Mohamad | `scoring/` | `TeamWorkings/Bahaa_Mohamad/HANDOFF.md` | `bahaa/scoring-validation` | B1 — input validation + tests |
| Ahmad Abualrub | `lab/` | `TeamWorkings/Ahmad_Abualrub/HANDOFF.md` | `ahmad/lab-parsing` | A1/A1b — `summarise()` + tests |
| Omar Abuzaid | `dashboard/` | `TeamWorkings/Omar_Abuzaid/HANDOFF.md` | `omar/findings-filter` | O1/O1b — `q` filter + tests |

### What each member does

1. Pull `build/full-system`.
2. Create their branch.
3. Paste their whole `HANDOFF.md` into Claude Code or another agent.
4. Review the diff.
5. Run `docker compose run --rm tools python -m pytest tests -q`.
6. Commit with their own name and email.
7. Add a row to the contribution log in their `TASKS.md`.
8. Push and open a pull request.

### Expected result

Each handoff adds its own tests on top of the 61. All four together produce
**84 passed**. A single handoff should pass 61 plus its own new tests.

### Merge order (suggested)

1. Talha (schema docs) — documentation only, lowest risk.
2. Bahaa (scoring validation) — touches scoring inputs.
3. Ahmad (lab parsing) — touches lab helper and a new test file.
4. Omar (dashboard filter) — touches the API query.

After each merge, pull `build/full-system` into the next branch, resolve
conflicts if any, and rerun the full suite.

---

## 5. Remaining work, in priority order

Copy this checklist into the chat when you resume.

### Priority 1 — Teammate contributions

- [ ] Replace placeholder GitHub handles in `.github/CODEOWNERS`.
- [ ] Replace `your-github-email@example.com` in Bahaa's, Ahmad's and Omar's
      `HANDOFF.md` and `TASKS.md`.
- [ ] Talha runs T5 and commits.
- [ ] Bahaa runs B1 and commits.
- [ ] Ahmad runs A1/A1b and commits.
- [ ] Omar runs O1/O1b and commits.
- [ ] Each member pushes and opens a PR.
- [ ] Review each PR against `CONTRIBUTING.md`.
- [ ] Merge all four into `build/full-system`.
- [ ] Confirm the suite is `84 passed` on `build/full-system`.
- [ ] Update `results.md` §7 and the README test count from 61 to 84.
- [ ] Update `TeamWorkings/README.md` if the dry-run wording needs to become
      "merged".

### Priority 2 — Submission plumbing

- [ ] Confirm the final GitHub repository is public or shared with the
      instructor.
- [ ] Merge `build/full-system` into `main`.
- [ ] Push `main`.
- [ ] Fresh-clone test: clone into a new folder, run the test suite, run E1.
- [ ] Tag the submission, for example `v1.0-submission`.
- [ ] Add a `LICENSE` file if the course requires one.
- [ ] Confirm `.gitignore` still excludes all generated data.
- [ ] Confirm no secrets or local paths are committed.

### Priority 3 — Demo and viva preparation

- [ ] Build a short slide deck: problem, method, E1–E6 results, limits.
- [ ] Write a 5-minute live demo script.
- [ ] Capture screenshots of the dashboard with real data.
- [ ] Prepare answers for likely questions (see §8).
- [ ] Rehearse the live commands once, end to end.
- [ ] Have a fallback: screenshots and `results.md` if the network fails.

### Priority 4 — Quality hardening

- [ ] Add a GitHub Actions workflow: build the image and run `pytest`.
- [ ] Add a short `README.md` inside each module.
- [ ] Add a reproducibility appendix to `REPORT.md` mapping each table to its
      command.
- [ ] Measure test coverage and record it.
- [ ] Run a linter and fix real issues only.
- [ ] Pin dependency versions in `requirements.txt` and the Dockerfile.

### Priority 5 — Strengthen the experiments (only if time allows)

- [ ] Run the full 1,000-domain E2 sample and report both scopes honestly.
- [ ] Repeat E3/E4/E5 three times and report variance, not one run.
- [ ] Add one more lab group or certificate type if it tests a real claim.
- [ ] Any new number goes into `results.md` with its command.
- [ ] Any new deviation goes into `DEVIATIONS.md`.

### Priority 6 — Report packaging

- [ ] Final proofread of `REPORT.md`.
- [ ] Check every figure and table matches `results.md`.
- [ ] Export to PDF with correct fonts, page numbers and headings.
- [ ] Check the PDF on a second machine.
- [ ] Submit the PDF, the repository link and the demo materials.

---

## 6. Placeholders that still need real values

| File | Placeholder | Replace with |
|---|---|---|
| `.github/CODEOWNERS` | `@bahaa-mohamad` | Bahaa's real GitHub handle |
| `.github/CODEOWNERS` | `@ahmad-abualrub` | Ahmad's real GitHub handle |
| `.github/CODEOWNERS` | `@omar-abuzaid` | Omar's real GitHub handle |
| `TeamWorkings/Bahaa_Mohamad/HANDOFF.md` | `your-github-email@example.com` | Bahaa's GitHub email |
| `TeamWorkings/Bahaa_Mohamad/TASKS.md` | `your-github-email@example.com` | Bahaa's GitHub email |
| `TeamWorkings/Ahmad_Abualrub/HANDOFF.md` | `your-github-email@example.com` | Ahmad's GitHub email |
| `TeamWorkings/Ahmad_Abualrub/TASKS.md` | `your-github-email@example.com` | Ahmad's GitHub email |
| `TeamWorkings/Omar_Abuzaid/HANDOFF.md` | `your-github-email@example.com` | Omar's GitHub email |
| `TeamWorkings/Omar_Abuzaid/TASKS.md` | `your-github-email@example.com` | Omar's GitHub email |

Talha's identity is already set: `Mohamad Talha Ezzo <talhaezzo2006@gmail.com>`.

Find any remaining placeholder:

```bash
git grep -n "example.com"
git grep -n "@bahaa-mohamad\|@ahmad-abualrub\|@omar-abuzaid"
```

---

## 7. Rules that must not change

These protect the integrity of the project.

1. **Docker only.** Do not run the crypto tooling natively.
2. **No invented numbers.** Every number comes from a command in `results.md`.
3. **Every deviation is recorded.** Add to `DEVIATIONS.md` in the same commit.
4. **No generated data in Git.** Databases, CSVs, certs, logs, charts stay out.
5. **One owner per module.** Cross-module changes need both owners.
6. **Real commits only.** Each member commits their own work under their own
   identity.
7. **`main` stays clean until submission.** Work on `build/full-system`.
8. **The hybrid lab handshake must be real.** If it fails, fall back and label
   it honestly. Never call a fallback "ok".

---

## 8. Likely viva questions and short answers

- **Why Mosca's inequality?** It turns "quantum risk" into a planning question:
  how long must the data stay secret (`X`), how long until a quantum computer
  arrives (`Z`), and how long migration takes (`Y`).
- **Why is the naive baseline there?** To show that a rule without context
  labels everything high and cannot prioritise. The contextual model moves
  60.3% of reachable hosts to low.
- **Why is E2 only 100 domains?** It is a reproducible sample, and the full
  1,000-domain command is documented. The limitation is stated in
  `DEVIATIONS.md` §5.2.
- **Why 73 of 100?** The other 27 are real survey outcomes: no DNS record,
  timeouts, or connections closed before a certificate. They are not scanner
  bugs; several were verified with DNS-over-HTTPS.
- **Why does hybrid TLS cost bytes but not time?** It adds one KEM ciphertext
  and public key, but no extra round trips.
- **Why is ML-DSA slower than ML-KEM?** Signing is a different operation from
  encapsulation; ML-DSA signatures are also much larger.
- **Why did E5 look wrong at first?** `openssl speed` divides by CPU time.
  Adding `-elapsed` made the constrained run honest. See `DEVIATIONS.md` §1.6.
- **What is the biggest limitation?** The scanner sees the handshake, not the
  organisation's data. Scores are planning prompts, not verified priorities.

---

## 9. File map for a new session

| Path | What it is |
|---|---|
| `README.md` | Project overview, commands, results at a glance |
| `REPORT.md` | Full written report |
| `results.md` | Every measured number and its command |
| `DEVIATIONS.md` | Every difference from the design guide |
| `CONTRIBUTING.md` | Branch, commit, test and review workflow |
| `NEXT_STEPS.md` | This file |
| `TeamWorkings/README.md` | Ownership model and handoff overview |
| `TeamWorkings/OWNERSHIP.md` | Path-to-owner map and cross-module protocol |
| `TeamWorkings/*/HANDOFF.md` | 30-minute task per member |
| `TeamWorkings/*/TASKS.md` | Full task queue and contribution log |
| `scanner/` | TLS inventory |
| `scoring/` | Risk model |
| `lab/` | Controlled ground truth and benchmarks |
| `dashboard/` | FastAPI app and charts |
| `tests/` | 61 tests |
| `docker/tools/Dockerfile` | Toolbox image (Debian 13, OpenSSL 3.5) |

---

## 10. Prompt to paste into a new session

```text
Read NEXT_STEPS.md first. Then read TeamWorkings/README.md.

We are on branch build/full-system at commit f3766d2. The suite is 61 passed.
The next milestone is the four teammate handoffs, then merge to main, then
submission packaging and demo prep.

Do not invent numbers. Do not commit generated data. Do not change main yet.
Work in Docker only. Tell me which checklist item you are doing before you
start.
```

---

## 11. How to keep this file honest

Update this file whenever one of these changes:

- the branch or last commit,
- the test count,
- a handoff is merged,
- a placeholder is replaced,
- `main` is merged,
- a new experiment number is added.

Keep the "Last verified" date current. A stale handoff file is worse than no
handoff file.
