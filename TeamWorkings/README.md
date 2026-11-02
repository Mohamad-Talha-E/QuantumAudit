# TeamWorkings — file ownership and commit guide

This folder records **who owns which part of QuantumAudit**. Each member has
their own folder containing the files for their area. The runnable project
stays at the repository root; these folders are the per-person record used to
show individual contribution in the GitHub commit history.

> **Before you commit:** only stage **your own** folder. Never run `git add .`
> from the repository root — that would put everyone's files into one person's
> commit. Commit only the area you actually worked on.

---

## 1. Folder map

| Member | Student ID | Area | Folder | Files |
|---|---|---|---|---:|
| Mohamad Talha Ezzo | 23000488 | Scanner and Data Engineering | `Mohamad_Talha_Ezzo/` | 14 |
| Bahaa Mohamad | 23001498 | Risk Analytics and Scoring | `Bahaa_Mohamad/` | 7 |
| Ahmad Abualrub | 23001599 | Lab and Cryptographic Benchmarking | `Ahmad_Abualrub/` | 7 |
| Omar Abuzaid | 23001809 | Dashboard and Documentation | `Omar_Abuzaid/` | 10 |

Total: **38 files**, which is every tracked source and documentation file in
the project. Generated data (databases, CSVs, certificates, logs, charts) is
deliberately **not** copied here and must not be committed.

---

## 2. Exact files in each folder

### Mohamad Talha Ezzo — Scanner and Data Engineering

```
TeamWorkings/Mohamad_Talha_Ezzo/
├── scanner/
│   ├── __init__.py
│   ├── cli.py          every experiment as one command
│   ├── db.py           SQLite schema and upserts
│   ├── kx.py           OpenSSL output parsing
│   ├── scan.py         one host = one handshake + one probe
│   └── tranco.py       download and seeded sampling
├── tests/
│   ├── conftest.py
│   ├── test_db.py
│   ├── test_kx.py
│   └── test_scan.py
├── .dockerignore
├── .gitignore
├── docker-compose.yml
└── requirements.txt
```

### Bahaa Mohamad — Risk Analytics and Scoring

```
TeamWorkings/Bahaa_Mohamad/
├── scoring/
│   ├── __init__.py
│   ├── mosca.py        contextual score + naive baseline
│   ├── rules.py        algorithm classifier
│   ├── score_db.py     apply a score to a whole run
│   └── sensitivity.py  the E6 scenario grid
└── tests/
    ├── test_mosca.py
    └── test_rules.py
```

### Ahmad Abualrub — Lab and Cryptographic Benchmarking

```
TeamWorkings/Ahmad_Abualrub/
├── lab/
│   ├── bench.py            E3 and E5 benchmarks
│   ├── e4_handshake.py     E4 hybrid overhead
│   ├── evaluate.py         E1 comparison
│   ├── genlab.sh           CA and certificate generator
│   ├── lab_manifest.json   ground truth for E1
│   └── start_lab.sh        20 TLS servers
└── docker/
    └── tools/
        └── Dockerfile      OpenSSL 3.5 toolbox image
```

### Omar Abuzaid — Dashboard and Documentation

```
TeamWorkings/Omar_Abuzaid/
├── dashboard/
│   ├── __init__.py
│   ├── app.py              FastAPI pages and JSON API
│   ├── charts.py           server-side matplotlib charts
│   ├── static/
│   │   └── style.css
│   └── templates/
│       └── index.html
├── tests/
│   └── test_dashboard.py
├── DEVIATIONS.md
├── README.md
├── REPORT.md
└── results.md
```

---

## 3. One-time setup (every member)

### Step 1 — Install Git and clone the repository

```bash
git clone https://github.com/Mohamad-Talha-E/QuantumAudit.git
cd QuantumAudit
```

If you already cloned it, just update:

```bash
git fetch origin
```

### Step 2 — Switch to the working branch

All work is on `build/full-system`, not `main`.

```bash
git checkout build/full-system
git pull origin build/full-system
```

> Talha must push the branch once before the others can fetch it:
> `git push -u origin build/full-system`

### Step 3 — Set **your own** Git identity

Use your real name and the email linked to your GitHub account. If the email
is not linked, GitHub will not show the commit under your profile.

```bash
git config --local user.name  "Your Full Name"
git config --local user.email "your-github-email@example.com"
```

Check it:

```bash
git config --local user.name
git config --local user.email
```

Use `--local` so this identity applies only to this repository.

---

## 4. Commit order

Do these **in order** so nobody has to resolve a conflict. Each member commits
one folder and pushes before the next member starts.

| Order | Member | Folder |
|---:|---|---|
| 1 | Mohamad Talha Ezzo | `TeamWorkings/Mohamad_Talha_Ezzo` |
| 2 | Bahaa Mohamad | `TeamWorkings/Bahaa_Mohamad` |
| 3 | Ahmad Abualrub | `TeamWorkings/Ahmad_Abualrub` |
| 4 | Omar Abuzaid | `TeamWorkings/Omar_Abuzaid` |

---

## 5. Step-by-step commit commands

### 5.1 Mohamad Talha Ezzo — Scanner and Data Engineering

```bash
git config --local user.name  "Mohamad Talha Ezzo"
git config --local user.email "talhaezzo2006@gmail.com"

git pull origin build/full-system
git add TeamWorkings/Mohamad_Talha_Ezzo
git status --short
git commit -m "feat(scanner): TLS inventory, Tranco sampling, database layer and integration config"
git push origin build/full-system
```

### 5.2 Bahaa Mohamad — Risk Analytics and Scoring

```bash
git config --local user.name  "Bahaa Mohamad"
git config --local user.email "bahaa@example.com"   # replace with your GitHub email

git pull origin build/full-system
git add TeamWorkings/Bahaa_Mohamad
git status --short
git commit -m "feat(scoring): algorithm classifier, Mosca risk model and E6 sensitivity analysis"
git push origin build/full-system
```

### 5.3 Ahmad Abualrub — Lab and Cryptographic Benchmarking

```bash
git config --local user.name  "Ahmad Abualrub"
git config --local user.email "ahmad@example.com"   # replace with your GitHub email

git pull origin build/full-system
git add TeamWorkings/Ahmad_Abualrub
git status --short
git commit -m "feat(lab): 20-server controlled lab, E1 ground truth and E3-E5 benchmarks"
git push origin build/full-system
```

### 5.4 Omar Abuzaid — Dashboard and Documentation

```bash
git config --local user.name  "Omar Abuzaid"
git config --local user.email "omar@example.com"    # replace with your GitHub email

git pull origin build/full-system
git add TeamWorkings/Omar_Abuzaid
git status --short
git commit -m "feat(dashboard): FastAPI app with charts, plus README, report and results"
git push origin build/full-system
```

> `git status --short` before the commit is a safety check. You should see
> **only your own folder** listed with `A` (added) entries. If you see another
> member's folder, stop and unstage it:
>
> ```bash
> git restore --staged TeamWorkings/Other_Member
> ```

---

## 6. Verify that your name is on your commit

After pushing, run:

```bash
git log --author="Bahaa Mohamad" --oneline -- TeamWorkings/Bahaa_Mohamad
```

You should see your own commit. To see the whole team at once:

```bash
git shortlog -sne -- TeamWorkings
```

Expected shape:

```
  1  Ahmad Abualrub <ahmad@example.com>
  1  Bahaa Mohamad <bahaa@example.com>
  1  Mohamad Talha Ezzo <talhaezzo2006@gmail.com>
  1  Omar Abuzaid <omar@example.com>
```

On GitHub, open **Insights → Contributors**, or open the folder and use the
**History** button. Each folder shows the member who committed it.

---

## 7. Troubleshooting

### Push rejected (`non-fast-forward`)

Someone pushed before you. Pull with rebase, then push again:

```bash
git pull --rebase origin build/full-system
git push origin build/full-system
```

### Wrong author on your last commit (not pushed yet)

```bash
git commit --amend --reset-author --no-edit
```

### Wrong author on a commit that is already pushed

Do **not** rewrite shared history. Either make a small follow-up commit with
the correct identity, or coordinate with the team before any rebase. A pushed
commit with the wrong author is not worth a force-push that breaks everyone
else's clone.

### You staged someone else's folder by accident

```bash
git restore --staged TeamWorkings/Other_Member
git status --short
```

### Git says "nothing to commit"

Your folder was already committed, possibly by someone else. Check:

```bash
git log --oneline -- TeamWorkings/Your_Name
```

If it is already in history under the wrong name, tell the team before making
further changes.

### Your commit does not appear on your GitHub profile

The email in `git config user.email` is not linked to your GitHub account. Add
that email in GitHub under **Settings → Emails**, or amend the commit with the
correct address before pushing.

---

## 8. What not to commit

These are generated and already ignored by `.gitignore`:

- `data/*.db`, `data/*.csv`, `data/tranco/`
- `lab/certs/`, `lab/servers/`, `lab/logs/`
- `dashboard/static/charts/`
- `__pycache__/`, `.pytest_cache/`

They are reproducible from the commands in `results.md`. Committing them would
bloat the repository and invite stale results.

---

## 9. After all four commits

The branch should contain four contribution commits on top of the build
commits. To confirm:

```bash
git log --oneline --graph --decorate -12
git shortlog -sne -- TeamWorkings
```

Then open a pull request from `build/full-system` into `main` on GitHub, or
merge locally once the team has reviewed the result.
