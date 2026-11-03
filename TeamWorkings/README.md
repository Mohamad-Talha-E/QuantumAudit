# TeamWorkings — ownership and real contribution

This folder is the team's **ownership and task board**. It does **not** contain
copies of the code.

Each member owns a live module at the repository root and commits real changes
to it: a feature, a test, a fix, or documentation. That is what makes the commit
history defensible — a commit that changes a module, adds a test and updates a
task log is evidence of work; a copied folder is not.

---

## Folder map

| Member | Student ID | Live module | 30-minute handoff | Task file |
|---|---|---|---|---|
| Mohamad Talha Ezzo | 23000488 | `scanner/` | [`Mohamad_Talha_Ezzo/HANDOFF.md`](Mohamad_Talha_Ezzo/HANDOFF.md) | [`TASKS.md`](Mohamad_Talha_Ezzo/TASKS.md) |
| Bahaa Mohamad | 23001498 | `scoring/` | [`Bahaa_Mohamad/HANDOFF.md`](Bahaa_Mohamad/HANDOFF.md) | [`TASKS.md`](Bahaa_Mohamad/TASKS.md) |
| Ahmad Abualrub | 23001599 | `lab/` | [`Ahmad_Abualrub/HANDOFF.md`](Ahmad_Abualrub/HANDOFF.md) | [`TASKS.md`](Ahmad_Abualrub/TASKS.md) |
| Omar Abuzaid | 23001809 | `dashboard/` | [`Omar_Abuzaid/HANDOFF.md`](Omar_Abuzaid/HANDOFF.md) | [`TASKS.md`](Omar_Abuzaid/TASKS.md) |

Each handoff was dry-run in a clean copy of the repository. Applying all four
gives **84 passing tests** (61 existing plus 23 new). A member only applies
their own handoff, so their branch adds that task's tests on top of the 61.

Supporting documents:

- [`OWNERSHIP.md`](OWNERSHIP.md) — every path mapped to its owner, the module
  dependency map, and the cross-module change protocol.
- [`../CONTRIBUTING.md`](../CONTRIBUTING.md) — the full workflow: branches,
  commits, tests, review and troubleshooting.
- [`../.github/CODEOWNERS`](../.github/CODEOWNERS) — GitHub's automatic review
  routing.

---

## How it works

1. Open **your** `HANDOFF.md` for a complete, 30-minute task with the exact
   change, test and commands. Paste it into Claude Code (or another coding
   agent), review the diff, and commit. Use `TASKS.md` for the full queue.
2. Create a branch named after yourself and the task, for example
   `bahaa/scoring-validation`.
3. Implement the change in the **live module** (for example `scoring/`).
4. Add or update a test that would fail without your change.
5. Run the full suite:
   ```bash
   docker compose run --rm tools python -m pytest tests -q
   ```
6. Commit under your own Git identity (see `CONTRIBUTING.md`).
7. Add a row to the **Contribution log** in your `TASKS.md`.
8. Push and open a pull request.

---

## Rules

- **One owner per module.** Only the owner, or a reviewer the owner asks,
  changes a module.
- **Cross-module changes need both owners.** If a scanner schema change affects
  `scoring/` or `dashboard/`, both owners review it.
- **No generated data.** Databases, CSVs, certificates, logs and charts stay
  out of Git.
- **No copied modules.** If you need a file for reference, open the live file;
  do not add a duplicate under `TeamWorkings/`.
- **Real commits only.** A commit should change behaviour, tests, or
  documentation in a way another person can review.

---

## Why this replaced the copied folders

An earlier draft put a copy of each module under a member's name. That is not
defensible: it duplicates code, drifts from the real module, and shows a commit
that adds a copy rather than a change. The current structure keeps one source
of truth per module, gives each member a real queue, and records ownership in
GitHub through `CODEOWNERS`.
