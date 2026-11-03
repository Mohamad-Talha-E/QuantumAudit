# Ahmad Abualrub — Lab and Cryptographic Benchmarking

**Student ID:** 23001599
**Owned paths:** `lab/`, `docker/tools/Dockerfile`
**Live module:** `lab/` at the repository root.

This file is your work queue and contribution log. Pick a task, implement it in
the live module, add tests, commit under your own Git identity, and record the
commit below.

---

## Tasks

| ID | Task | Acceptance criteria | Status |
|---|---|---|---|
| A1 | **Report benchmark variance.** Run each measurement several times and report mean, standard deviation, minimum and maximum alongside ops/sec. | `lab/bench.py` emits the extra columns; a pure `summarise(samples)` helper is unit-tested; E3 and E5 tables in `results.md` are regenerated with the new columns. | ☐ |
| A2 | **Add a lab readiness check.** Verify that all expected ports answer with the expected protocol and certificate before E1 runs. | New `lab/verify_lab.py` exits non-zero and names the failing port; `lab/evaluate.py` calls it first; a unit test uses a fake probe. | ☐ |
| A3 | **Add a `SecP384r1MLKEM1024` server.** Extend the lab to cover the larger hybrid group, and update the manifest and E1 expectations. | `genlab.sh`, `start_lab.sh` and `lab_manifest.json` agree; E1 still reports 100% exact match on the new total; `results.md` is updated. | ☐ |
| A4 | **Add a TLS 1.2 parsing regression test.** Capture real `Server Temp Key` output and assert the group mapping. | New case in `tests/test_kx.py` covering `Server Temp Key: ECDH, P-384, 384 bits` and the `prime256v1` alias. | ☐ |
| A5 | **Document the lab.** Add `lab/README.md` explaining certificate regeneration, server layout, and the E1/E3/E4/E5 commands. | A reader can rebuild the lab from scratch using only the document; every command is copy-pasteable. | ☐ |

---

## Contribution log

| Date | Commit | Task | What changed | Tests |
|---|---|---|---|---|
| | | | | |

---

## Commit workflow

```bash
git config --local user.name  "Ahmad Abualrub"
git config --local user.email "your-github-email@example.com"

git checkout -b ahmad/bench-variance
# implement A1 in lab/ and tests/
docker compose run --rm tools python -m pytest tests -q
git add lab tests
git commit -m "feat(lab): report benchmark variance for E3 and E5"
git push -u origin ahmad/bench-variance
```

Then update this file with the commit hash and open a pull request.

## Definition of done

- [ ] Code lives in the live module, not a copy.
- [ ] At least one new or updated test covers the change.
- [ ] `docker compose run --rm tools python -m pytest tests -q` passes.
- [ ] The lab still starts and E1 still passes when the change touches `lab/`.
- [ ] `lab/README.md` is updated when the layout or commands change.
- [ ] No generated certificates, server directories or logs are committed.
- [ ] The contribution log above has a row for the commit.
