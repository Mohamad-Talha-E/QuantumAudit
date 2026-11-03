# QuantumAudit

**A TLS cryptographic inventory scanner, a quantum-risk scorer, a post-quantum
benchmark lab, and a dashboard — in one reproducible Docker setup.**

QuantumAudit answers a practical question: *which of our servers need to move to
post-quantum cryptography first, and what will that move cost?*

It does three things:

1. **Looks** at what cryptography a server actually uses during a TLS handshake.
2. **Scores** how urgent that is, using Mosca's inequality and stated planning
   assumptions — not a single scary headline.
3. **Measures** what classical and post-quantum algorithms cost in time and
   bytes, in a controlled lab.

The results are shown in a web dashboard and stored in SQLite.

> This repository contains the full implementation and all six experiments
> (E1–E6). Every number in `results.md` and `REPORT.md` was measured by this
> code. Nothing is estimated or copied from the design guide. Every deviation
> from that guide is recorded in [`DEVIATIONS.md`](DEVIATIONS.md).

---

## Why this is not just "RSA is broken"

A TLS handshake tells you *what* a server uses. It cannot tell you *how much
that matters*, because urgency depends on how long the data must stay secret
(X), how long migration takes (Y), and when a quantum computer arrives (Z).

Mosca's inequality says the danger exists when **X + Y > Z**.

QuantumAudit makes X, Y and Z explicit. Change them, and you can see exactly
which hosts change verdict — that is experiment **E6**. A naive rule that flags
every RSA/ECC host is included as a baseline to show what is lost when context
is ignored.

---

## Quick start

You need **Docker** and **Docker Compose**. Nothing else. No local OpenSSL, no
local Python packages, no platform-specific setup.

```bash
# 1. Build the toolbox image (once)
docker compose build

# 2. Start the controlled lab (20 TLS servers on ports 8443-8462)
docker compose up -d lab

# 3. Check the scanner against the lab (E1)
docker compose run --rm tools python -m lab.evaluate
docker compose run --rm tools python -m scanner.cli scan-lab --run-id e1-lab --fresh
docker compose run --rm tools python -m scanner.cli score --run-id e1-lab --all-scenarios

# 4. Run the public survey (E2) - about 10 minutes
docker compose run --rm tools python -m scanner.cli scan-tranco \
    --n 100 --seed 413 --pool 10000 --run-id e2-tranco
docker compose run --rm tools python -m scanner.cli score \
    --run-id e2-tranco --all-scenarios

# 5. Start the dashboard
docker compose up -d dashboard
# open http://localhost:8000
```

To stop everything:

```bash
docker compose down
```

### Windows note

On PowerShell, use `${PWD}` where a command below shows `$PWD`. On `cmd.exe`,
use `%cd%`. The `docker compose` commands work unchanged.

---

## What is in the box

```
QuantumAudit/
├── scanner/            TLS inventory
│   ├── scan.py         one host = one handshake + one openssl probe
│   ├── kx.py           parses OpenSSL output (groups, protocol, cipher)
│   ├── db.py           SQLite schema and upserts
│   ├── tranco.py       downloads and samples the Tranco list
│   └── cli.py          every experiment as one command
├── scoring/            risk model
│   ├── rules.py        algorithm classifier
│   ├── mosca.py        contextual score + naive baseline
│   ├── score_db.py     applies the score to a whole run
│   └── sensitivity.py  the E6 grid
├── lab/                controlled ground truth
│   ├── genlab.sh       builds a CA and six certificate types
│   ├── start_lab.sh    starts 20 TLS servers
│   ├── lab_manifest.json  known answers for E1
│   ├── evaluate.py     E1 comparison
│   ├── bench.py        E3 and E5 benchmarks
│   └── e4_handshake.py E4 hybrid overhead
├── dashboard/          FastAPI + matplotlib
│   ├── app.py          pages and JSON API
│   ├── charts.py       server-side PNG charts
│   └── templates/      single-page UI
├── tests/              61 tests
├── docker/tools/       the toolbox image
├── results.md          every measured number
├── REPORT.md           the written report
└── DEVIATIONS.md       every difference from the design guide
```

### Architecture

```
                    +-----------------------------+
                    |  Tranco top-1M list (CSV)   |
                    +--------------+--------------+
                                   | seeded sample
                                   v
 +----------------+      +---------+----------+      +------------------+
 |  Public hosts  |<---->|  scanner/scan.py   |<---->|  lab/ (20 TLS)   |
 |  :443          |      |  2 handshakes/host |      |  :8443-8462      |
 +----------------+      +---------+----------+      +------------------+
                                   | findings
                                   v
                    +-----------------------------+
                    |   SQLite: findings, scores  |
                    |   and bench tables          |
                    +--------------+--------------+
                                   | read
                                   v
                    +-----------------------------+
                    |  scoring/ (Mosca + naive)   |
                    |  dashboard/ (FastAPI + PNG) |
                    +-----------------------------+
```

---

## Commands

All commands run inside the `tools` container, so they are identical on
Windows, macOS and Linux.

| What | Command |
|---|---|
| Scanner help | `docker compose run --rm tools python -m scanner.cli --help` |
| Scan the lab (E1) | `... scan-lab --run-id e1-lab --fresh` |
| Scan a Tranco sample (E2) | `... scan-tranco --n 100 --seed 413 --pool 10000` |
| Scan your own list | `... scan-list targets.txt --run-id my-run` |
| Score one scenario | `... score --run-id e2-tranco` |
| Score every scenario | `... score --run-id e2-tranco --all-scenarios` |
| Sensitivity table (E6) | `... sensitivity --run-id e2-tranco` |
| Run overview | `... summary --run-id e2-tranco --errors` |
| Algorithm benchmark (E3) | `python -m lab.bench --run-id e3-bench` |
| Hybrid overhead (E4) | `python -m lab.e4_handshake` |
| Constrained benchmark (E5) | `python -m lab.bench --constrained --run-id e5-constrained` |
| Tests | `python -m pytest tests -q` |

### Full 1,000-domain run (optional)

The report uses a seeded 100-domain sample. The full run is one command and is
documented as a scope decision in [`DEVIATIONS.md`](DEVIATIONS.md) §5.2:

```bash
docker compose run --rm tools python -m scanner.cli scan-tranco \
    --n 1000 --seed 413 --pool 10000 --run-id e2-tranco-1000 --delay 0.5
```

---

## Results at a glance

| Experiment | Result |
|---|---|
| **E1 — scanner accuracy** | 20/20 exact match; precision = recall = F1 = **1.00** |
| **E2 — public survey** | 73/100 reachable; **44 (60.3%)** already use hybrid `X25519MLKEM768`; **29** are classical-only |
| **E3 — algorithms** | ML-KEM-768 encaps **0.0237 ms** (8× faster than RSA-2048 sign); ML-DSA-65 sign **0.7117 ms** |
| **E4 — hybrid handshake** | **+0.8% time**, **+80.9% bytes** versus classical TLS 1.3 |
| **E5 — constrained** | 0.5 CPU / 256 MB roughly **halves** throughput for every algorithm, classical and PQ alike |
| **E6 — sensitivity** | **29 of 73** hosts (39.7%) change risk class between extreme planning scenarios; the naive rule calls all 73 high |

Full tables, environment details and the commands that produced them are in
[`results.md`](results.md).

---

## How the score works

Every host is put into one of four algorithm classes:

| Class | Meaning | Example |
|---|---|---|
| `vulnerable` | Classical asymmetric crypto only | RSA cert + X25519 exchange |
| `hybrid` | Some post-quantum, some classical | RSA cert + X25519MLKEM768 exchange |
| `resistant` | Post-quantum everywhere | ML-DSA cert + MLKEM768 exchange |
| `weakened` | Weak symmetric crypto | AES-128, 3DES, RC4 |
| `unknown` | Not enough evidence | handshake failed |

Then the contextual rule applies Mosca's inequality:

```
safe window = Z - Y
if class is hybrid or resistant      -> low
if shelf life <= safe window         -> low
if shelf life <= safe window + 3y    -> medium
otherwise                            -> high
```

The **naive baseline** ignores X, Y and Z: everything that still contains
classical asymmetric crypto (`vulnerable` and `hybrid`) is high. It is
deliberately crude, and that is the point of comparing against it.

Each score stores its **reason** and a **next step**, so a reader can disagree
with the assumptions rather than with an unexplained number.

---

## Ethics and limits

- **Handshake only.** The scanner completes one TLS handshake per host. It
  never sends an HTTP request, never stores payload, and never attempts to
  attack or decrypt anything.
- **Rate limited.** The public scan waits 0.5 s between hosts.
- **Snapshot, not a census.** Tranco membership and server configuration
  change. The seed makes the *sample* reproducible, not the *results*.
- **Illustrative scores.** A per-domain score is not a verified
  organisation-specific priority. It is a planning prompt.
- **Lab is isolated.** All server experiments run in Docker with no real user
  data.

Known technical limitations are listed at the end of
[`DEVIATIONS.md`](DEVIATIONS.md), including best-effort TLS 1.2 group
detection and the fact that lab ML-DSA certificates are signed by an RSA CA.

---

## Documentation

| File | Contents |
|---|---|
| [`REPORT.md`](REPORT.md) | Full written report: literature, method, results, discussion |
| [`results.md`](results.md) | Every measured number and the command that produced it |
| [`DEVIATIONS.md`](DEVIATIONS.md) | Every difference from the design guide, with reasons |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Branch, commit, test and review workflow |
| [`TeamWorkings/README.md`](TeamWorkings/README.md) | Module ownership, task queues and contribution rules |

---

## Course

CSCY413 — Special Topics in Cybersecurity
Group Project, Track: Post-Quantum and Quantum-Safe Security
Instructor: Dr. Sapna Sadhwani
