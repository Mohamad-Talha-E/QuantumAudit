# Project instructions — QuantumAudit

## Start here

Read [`NEXT_STEPS.md`](NEXT_STEPS.md) before doing anything. It holds the
current branch, commit, test count, remaining checklist and exact experiment
commands.

Then read [`TeamWorkings/README.md`](TeamWorkings/README.md) for module
ownership.

## Hard rules

- **Docker only.** All crypto and Python runs inside the `tools` container.
  Native Windows lacks OpenSSL 3.5 and ML-KEM.
- **No invented numbers.** Every number must come from a command recorded in
  `results.md`.
- **Record every deviation** from the design guide in `DEVIATIONS.md`.
- **No generated data in Git.** Databases, CSVs, certificates, logs and charts
  are reproducible and ignored.
- **One owner per module.** See `TeamWorkings/OWNERSHIP.md` before editing
  another member's module.
- **Real commits only.** Each member commits their own work under their own Git
  identity. Never author a commit for a teammate.
- **Do not merge to `main`** until the submission checklist says so. Work on
  `build/full-system`.

## Current state

- Branch: `build/full-system`
- Last commit: `f3766d2`
- Tests: `61 passed`
- `main`: untouched

## Common commands

```bash
docker compose build tools
docker compose run --rm tools python -m pytest tests -q
docker compose up -d lab
docker compose run --rm tools python -m lab.evaluate
docker compose run --rm tools python -m scanner.cli scan-tranco \
    --n 100 --seed 413 --pool 10000 --run-id e2-tranco
docker compose run --rm tools python -m scanner.cli score \
    --run-id e2-tranco --all-scenarios
docker compose run --rm tools python -m scanner.cli sensitivity \
    --run-id e2-tranco
docker compose run --rm tools python -m lab.bench --run-id e3-bench
docker compose run --rm tools python -m lab.e4_handshake
docker compose down
```

## Style

- Plain, short sentences in documentation.
- Keep changes consistent with the module you are editing.
- Add or update a test for every behaviour change.
- Update `NEXT_STEPS.md` when the branch, test count or checklist changes.
