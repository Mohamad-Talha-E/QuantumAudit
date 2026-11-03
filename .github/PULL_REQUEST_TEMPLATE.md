## Summary

<!-- One or two sentences: what does this change do, and why? -->

## Task

- Task ID (from `TeamWorkings/<Name>/TASKS.md`):
- Module:
- Owner:

## What changed

<!-- List the files or behaviour that changed. -->

## Tests

<!-- Paste the command and the result. -->

```
docker compose run --rm tools python -m pytest tests -q
```

## Checklist

- [ ] The change is in the live module, not a copy.
- [ ] A test would fail without this change.
- [ ] The full test suite passes.
- [ ] Documentation is updated if behaviour or numbers changed.
- [ ] No generated data, certificates, logs or charts are committed.
- [ ] The contribution log in my `TASKS.md` has a row for this commit.

## Cross-module impact

<!-- Does this touch another member's module? If yes, name it and tag the owner. -->

- [ ] This change stays inside one module.
- [ ] This change crosses modules and both owners are tagged.
