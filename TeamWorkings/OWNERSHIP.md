# Ownership map

Every tracked path has exactly one owner. Ownership means: you are the default
reviewer, you keep the module working, and you decide when a change to it is
ready.

---

## 1. Path ownership

| Path | Owner | Task file |
|---|---|---|
| `scanner/` | Mohamad Talha Ezzo | `TeamWorkings/Mohamad_Talha_Ezzo/TASKS.md` |
| `tests/conftest.py` | Mohamad Talha Ezzo | same |
| `tests/test_db.py` | Mohamad Talha Ezzo | same |
| `tests/test_kx.py` | Mohamad Talha Ezzo | same |
| `tests/test_scan.py` | Mohamad Talha Ezzo | same |
| `docker-compose.yml` | Mohamad Talha Ezzo | same |
| `requirements.txt` | Mohamad Talha Ezzo | same |
| `.dockerignore`, `.gitignore` | Mohamad Talha Ezzo | same |
| `scoring/` | Bahaa Mohamad | `TeamWorkings/Bahaa_Mohamad/TASKS.md` |
| `tests/test_rules.py` | Bahaa Mohamad | same |
| `tests/test_mosca.py` | Bahaa Mohamad | same |
| `lab/` | Ahmad Abualrub | `TeamWorkings/Ahmad_Abualrub/TASKS.md` |
| `docker/tools/` | Ahmad Abualrub | same |
| `dashboard/` | Omar Abuzaid | `TeamWorkings/Omar_Abuzaid/TASKS.md` |
| `tests/test_dashboard.py` | Omar Abuzaid | same |
| `README.md` | Omar Abuzaid | same |
| `REPORT.md` | Omar Abuzaid | same |
| `results.md` | Omar Abuzaid | same |
| `DEVIATIONS.md` | Omar Abuzaid | same |
| `CONTRIBUTING.md`, `TeamWorkings/` | All members (shared) | — |

Shared files (`CONTRIBUTING.md`, `TeamWorkings/`) may be edited by any member,
but a change to the rules needs agreement from all four.

---

## 2. Module dependency map

```
lab/  ──────────────►  scanner/  ──────────►  scoring/  ──────────►  dashboard/
(E1 ground truth)      (findings)            (verdicts)             (views)
```

- `lab/` produces the known answers that `scanner/` is tested against.
- `scanner/` writes `findings`; `scoring/` reads them and writes `scores`.
- `dashboard/` reads both tables and the E6 table.

The arrows show data flow, not permission. A change that crosses an arrow needs
both owners to review.

---

## 3. Cross-module change protocol

Some changes cannot stay inside one module. Examples:

- Adding a column to `findings` (`scanner/db.py`) affects `scoring/score_db.py`
  and `dashboard/app.py`.
- Changing a score threshold (`scoring/mosca.py`) changes dashboard verdicts and
  the E6 tables in `results.md`.
- Adding a lab server (`lab/`) changes the E1 expected count in the report.

Protocol:

1. Open an issue or a draft pull request that names both modules.
2. Tag both owners in the description.
3. Keep the change in one pull request so the interface change and its
   consumers move together.
4. Both owners approve before merge.
5. Update `results.md` or `REPORT.md` if a number changes.

---

## 4. Review expectations

- The owner of a touched module is the required reviewer.
- A reviewer checks four things: the change is in the live module, a test would
  fail without it, the suite passes, and no generated data is included.
- Reviews should happen within two working days so the team is not blocked.
- If the owner is unavailable, another member may review, but the owner should
  look at it afterwards.

---

## 5. GitHub enforcement

`CODEOWNERS` asks the right person to review automatically. It does not stop a
merge on its own; branch protection does that. Recommended settings for
`build/full-system` and `main`:

- Require a pull request before merging.
- Require at least one approval.
- Require review from Code Owners.
- Dismiss stale approvals when new commits are pushed.

The repository owner (Talha) can enable these under **Settings → Branches**.
