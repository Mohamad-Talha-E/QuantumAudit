# Database schema

The schema is defined in `scanner/db.py`. The database is SQLite. There are
three tables. A generated database lives in `data/` and is never committed.

## `findings`

One row per host per scan run. It stores raw handshake facts only: what the
server actually negotiated. It never stores payload.

| column | type | meaning |
|---|---|---|
| `id` | INTEGER | primary key |
| `run_id` | TEXT | experiment name, for example `e2-tranco` |
| `host` | TEXT | hostname or IP address that was scanned |
| `port` | INTEGER | TCP port, default 443 |
| `profile` | TEXT | `public` or `lab` (which trust store was used) |
| `scan_time` | TEXT | UTC timestamp of the scan |
| `protocol` | TEXT | negotiated TLS version, for example `TLSv1.3` |
| `cipher` | TEXT | negotiated cipher suite |
| `kx_group` | TEXT | negotiated key-exchange group |
| `cert_alg` | TEXT | certificate public-key algorithm |
| `key_size` | INTEGER | certificate key size in bits |
| `sig_alg` | TEXT | certificate signature algorithm |
| `cert_expiry` | TEXT | certificate expiry date |
| `hybrid_flag` | INTEGER | 1 when the key exchange mixes post-quantum and classical |
| `status` | TEXT | `ok` or `error` |
| `error` | TEXT | failure message when `status = 'error'`, otherwise NULL |

The natural key is `(run_id, host, port)`. Re-scanning the same host in the
same run uses `ON CONFLICT (run_id, host, port) DO UPDATE`, so the existing row
is refreshed instead of being silently ignored or duplicated.

Rows with `status = 'error'` are kept on purpose. They record which hosts could
not be reached and why, which is part of the E2 result: a failed host is a
finding about coverage, not a reason to lose the row.

## `scores`

One row per finding **per planning scenario**. A finding can have several
scores because the Mosca verdict depends on the assumed shelf life, migration
time and quantum horizon.

| column | type | meaning |
|---|---|---|
| `finding_id` | INTEGER | foreign key to `findings.id` |
| `scenario` | TEXT | scenario key, for example `x15_y3_z15` |
| `shelf_life_years` | INTEGER | how long the data must stay secret |
| `migration_years` | INTEGER | assumed time to migrate |
| `quantum_years` | INTEGER | assumed time until a quantum computer |
| `alg_class` | TEXT | `hybrid`, `resistant`, `vulnerable`, `weakened` or `unknown` |
| `score_naive` | TEXT | baseline verdict with no timeline |
| `score_contextual` | TEXT | Mosca-based verdict |
| `reason` | TEXT | one-line explanation of the verdict |
| `migration_step` | TEXT | recommended next step |

The primary key is `(finding_id, scenario)`. Scores are deleted automatically
when their finding is deleted (`ON DELETE CASCADE`).

## `bench`

One row per measured operation, plus one row per measured size. E3 and E5
share this table; `constrained` says which run it came from.

| column | type | meaning |
|---|---|---|
| `id` | INTEGER | primary key |
| `run_id` | TEXT | `e3-bench` or `e5-bench` |
| `algo` | TEXT | algorithm label, for example `ML-KEM-768` |
| `op` | TEXT | operation or field, for example `encaps` or `ciphertext` |
| `ops_per_s` | REAL | operations per second (NULL for a size row) |
| `mean_ms` | REAL | milliseconds per operation (NULL for a size row) |
| `bytes` | INTEGER | size in bytes (NULL for a timing row) |
| `constrained` | INTEGER | 1 for the E5 constrained run, 0 for E3 |
| `ts` | TEXT | UTC timestamp of the measurement |

## Why two tables instead of one

The original design used a single `reason` column for two different things: why
a scan failed, and why a host scored high. Those are different facts with
different lifetimes. Splitting `findings` (scan facts) from `scores` (verdicts
per scenario) keeps each row honest and lets one finding carry many verdicts.
