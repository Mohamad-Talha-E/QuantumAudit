# Results

All numbers below were produced by this repository on the machine described in
§0. Nothing is copied from the design guide or estimated. Every table can be
regenerated with the command shown above it.

---

## 0. Environment

| Item | Value |
|---|---|
| Runtime | Docker 29.9.2, container `quantumaudit/tools:latest` |
| Base image | `debian:13-slim` |
| OpenSSL | 3.5.7 (native ML-KEM, ML-DSA, hybrid TLS groups) |
| Python | 3.13.5 |
| `cryptography` | 50.0.2 |
| Host CPU | 12 logical cores |
| Host memory | ~7.9 GB |
| Database | SQLite, `data/quantumaudit.db` |

Two timing modes are reported. **E3** runs unconstrained. **E5** runs the same
code with `--cpus=0.5 --memory=256m`. Both use `openssl speed -elapsed`, so
throughput is per **wall-clock second**, not per CPU-second.

---

## 1. E1 — Scanner accuracy against the lab

Command:

```bash
docker compose up -d lab
docker compose run --rm tools python -m lab.evaluate
```

Twenty controlled servers on ports 8443–8462. The scanner's output is compared
field by field with `lab/lab_manifest.json`.

| Field | Accuracy |
|---|---|
| protocol | 100.0% |
| cert_alg | 100.0% |
| key_size | 100.0% |
| kx_group | 100.0% |
| hybrid_flag | 100.0% |
| **Whole row exact** | **100.0% (20/20)** |

Post-quantum detection (the binary decision the risk score depends on):

| Metric | Value | Target |
|---|---|---|
| Precision | **1.00** | ≥ 0.80 |
| Recall | **1.00** | ≥ 0.80 |
| F1 | **1.00** | — |

The lab deliberately includes awkward cases: TLS 1.2, pure ML-KEM (no classical
fallback), the `SecP256r1MLKEM768` hybrid group, ML-DSA-65 certificates,
Ed25519, X448 and an AES-128-only host. A perfect score therefore means the
scanner distinguishes these cases, not merely that it can reach a server.

---

## 2. E2 — Real-world TLS survey

Command:

```bash
docker compose run --rm tools python -m scanner.cli scan-tranco \
    --n 100 --seed 413 --pool 10000 --run-id e2-tranco
docker compose run --rm tools python -m scanner.cli score \
    --run-id e2-tranco --all-scenarios
```

Sample: 100 domains drawn with seed 413 from the top 10,000 of Tranco
(1,000,000 entries downloaded). The sample is reproducible.

### 2.1 Reachability

| Outcome | Hosts |
|---|---|
| Reachable, handshake completed | **73** |
| No DNS record (no A/AAAA) | 20 |
| Connection timeout | 4 |
| TLS connection closed before certificate | 3 |
| **Total sampled** | **100** |

The 27 failures are real survey data, not scanner errors. Verified with a
public DNS-over-HTTPS resolver: several failed names (`msecnd.net`,
`zooplus.net`, `kameleoon.io`) return `NOERROR` with **no A, AAAA or CNAME
record** — they are registered names that do not serve a website. Tranco ranks
traffic to any subdomain, so the apex name need not be a web server.

Adoption percentages below use **73**, the number of hosts that answered.

### 2.2 Negotiated key exchange

| Group | Hosts | Share |
|---|---|---|
| **X25519MLKEM768** (hybrid, post-quantum) | **44** | **60.3%** |
| X25519 (classical) | 17 | 23.3% |
| P-256 (classical) | 10 | 13.7% |
| P-384 (classical) | 1 | 1.4% |
| RSA (static, no forward secrecy) | 1 | 1.4% |

### 2.3 Protocol and certificate algorithms

| Protocol | Hosts |
|---|---|
| TLS 1.3 | 60 (82.2%) |
| TLS 1.2 | 13 (17.8%) |

| Certificate key | Hosts |
|---|---|
| RSA | 51 (69.9%) |
| EC | 22 (30.1%) |

No sampled public host used an ML-DSA certificate, which matches deployment
reality: post-quantum **key exchange** is being rolled out, post-quantum
**authentication** is not yet.

### 2.4 Risk classification

| Model | Low | Medium | High |
|---|---|---|---|
| Naive rule (no context) | 0 | 0 | **73** |
| Contextual, default `x15_y3_z15` | **44** | 0 | **29** |

Algorithm classes: **44 hybrid**, **29 vulnerable**.

The contextual model moves 44 hosts (60.3%) from "high" to "low" because their
data does not need to stay secret longer than the safe window left after
migration. This is the central E2 result: *a handshake alone cannot prioritise
migration; the planning assumptions matter as much as the algorithm.*

> Illustrative only. These are per-domain observations, not verified
> organisation-specific priorities.

---

## 3. E3 — Classical vs post-quantum algorithms

Command:

```bash
docker compose run --rm tools python -m lab.bench --run-id e3-bench
```

`openssl speed -elapsed -seconds 2`. Mean milliseconds are `1000 / ops_per_s`.

### 3.1 Throughput

| Algorithm | Operation | ops/sec | Mean ms |
|---|---|---:|---:|
| RSA-2048 | keygen | 32 | 31.5457 |
| RSA-2048 | sign | 5,194 | 0.1925 |
| RSA-2048 | verify | 78,746 | 0.0127 |
| ECDH P-256 | derive | 28,370 | 0.0352 |
| X25519 | derive | 41,635 | 0.0240 |
| ECDSA P-256 | sign | 66,264 | 0.0151 |
| ECDSA P-256 | verify | 21,892 | 0.0457 |
| ML-KEM-768 | keygen | 30,105 | 0.0332 |
| ML-KEM-768 | **encaps** | **42,138** | **0.0237** |
| ML-KEM-768 | decaps | 28,657 | 0.0349 |
| ML-DSA-65 | keygen | 7,632 | 0.1310 |
| ML-DSA-65 | **sign** | **1,405** | **0.7117** |
| ML-DSA-65 | verify | 7,690 | 0.1300 |

### 3.2 Sizes (bytes)

| Algorithm | Public key | Private key | Ciphertext / signature |
|---|---:|---:|---:|
| ML-KEM-768 | 1,206 | 2,498 | 1,088 (ciphertext) |
| ML-DSA-65 | 1,974 | 4,098 | 3,309 (signature) |
| RSA-2048 | 294 | 1,192 | 256 (signature) |
| ECDSA P-256 | 91 | 121 | 71 (signature) |
| ECDH P-256 | 91 | 121 | — |
| X25519 | 44 | 48 | — |

ML-KEM-768 encapsulation is **8× faster than RSA-2048 signing** (0.024 ms vs
0.193 ms) and produces a 1,088-byte ciphertext instead of a 256-byte
signature. ML-DSA-65 signing is the slowest operation measured (0.71 ms) and
its signature is 12.9× larger than RSA-2048's.

---

## 4. E4 — Hybrid handshake overhead

Command:

```bash
docker compose run --rm tools python -m lab.e4_handshake
```

Two lab servers that differ only in key-exchange group: port 8443 (X25519) and
port 8447 (X25519 + ML-KEM-768). Timing with `openssl s_time -new`; byte counts
sum TLS message lengths up to the first application-data record.

| Handshake | Handshakes/sec | Mean ms | Handshake bytes |
|---|---:|---:|---:|
| TLS 1.3 classical (X25519) | 2,501 | 0.400 | 2,207 |
| TLS 1.3 hybrid (X25519+ML-KEM-768) | 2,482 | 0.403 | 3,993 |

| Delta | Value |
|---|---|
| Time | **+0.003 ms** per handshake (+0.8%) |
| Bytes | **+1,786 bytes** per handshake (+80.9%) |

The hybrid transition is almost free in **time** and expensive in **bytes**.
That is the expected trade-off: one extra KEM ciphertext and public key, no
extra round trips.

---

## 5. E5 — Constrained resources

Command:

```bash
docker run --rm --cpus=0.5 --memory=256m \
    -v "$PWD:/app" -w /app quantumaudit/tools:latest \
    python -m lab.bench --constrained --run-id e5-constrained
```

| Algorithm | Operation | ops/sec | Mean ms | Slowdown vs E3 |
|---|---|---:|---:|---:|
| RSA-2048 | keygen | 14 | 69.9301 | 2.29× |
| RSA-2048 | sign | 2,638 | 0.3791 | 1.97× |
| RSA-2048 | verify | 39,675 | 0.0252 | 1.98× |
| ECDH P-256 | derive | 14,392 | 0.0695 | 1.97× |
| X25519 | derive | 20,660 | 0.0484 | 2.02× |
| ECDSA P-256 | sign | 33,238 | 0.0301 | 1.99× |
| ECDSA P-256 | verify | 11,005 | 0.0909 | 1.99× |
| ML-KEM-768 | keygen | 15,062 | 0.0664 | 2.00× |
| ML-KEM-768 | encaps | 21,055 | 0.0475 | 2.00× |
| ML-KEM-768 | decaps | 14,400 | 0.0694 | 1.99× |
| ML-DSA-65 | keygen | 3,803 | 0.2630 | 2.01× |
| ML-DSA-65 | sign | 676 | 1.4804 | 2.08× |
| ML-DSA-65 | verify | 3,857 | 0.2593 | 1.99× |

Halving the CPU halves throughput almost exactly, for **both** classical and
post-quantum algorithms. The post-quantum algorithms therefore scale the same
way as the classical ones: no algorithm has a pathological behaviour under
constraint. ML-KEM-768 encapsulation still costs only 0.048 ms on half a core.

An earlier E5 run produced numbers identical to E3 because `openssl speed`
divides by CPU time. Adding `-elapsed` fixed the measurement; see
`DEVIATIONS.md` §1.6.

---

## 6. E6 — Sensitivity analysis

Command:

```bash
docker compose run --rm tools python -m scanner.cli sensitivity --run-id <run>
```

Migration time is fixed at **3 years**. Shelf life varies over 5/10/15/25
years; quantum horizon over 10/15/20 years.

### 6.1 Lab run (20 hosts)

| Metric | Value |
|---|---|
| Hosts scored | 20 |
| Algorithm classes | 13 vulnerable, 7 hybrid |
| Naive rule: high | 20 (100%) |
| Contextual, `x15_y3_z15` | 13 high, 7 low |
| Verdict changes, `x5_z20` → `x25_z10` | **13** |

### 6.2 Tranco run (73 reachable hosts)

| Metric | Value |
|---|---|
| Hosts scored | 73 |
| Algorithm classes | 44 hybrid, 29 vulnerable |
| Naive rule: high | 73 (100%) |
| Contextual, `x15_y3_z15` | 29 high, 44 low |
| Verdict changes, `x5_z20` → `x25_z10` | **29** |

### 6.3 Full grid — Tranco run

| Shelf life / horizon | low | medium | high |
|---|---:|---:|---:|
| x5_z10 | 44 | 29 | 0 |
| x5_z15 | 73 | 0 | 0 |
| x5_z20 | 73 | 0 | 0 |
| x10_z10 | 44 | 0 | 29 |
| x10_z15 | 44 | 29 | 0 |
| x10_z20 | 73 | 0 | 0 |
| x15_z10 | 44 | 0 | 29 |
| x15_z15 | 44 | 0 | 29 |
| x15_z20 | 44 | 29 | 0 |
| x25_z10 | 44 | 0 | 29 |
| x25_z15 | 44 | 0 | 29 |
| x25_z20 | 44 | 0 | 29 |

The 44 hybrid hosts are always low: their key exchange is already
post-quantum. The 29 vulnerable hosts move between low, medium and high as the
assumptions change. A single "high risk" headline is therefore unstable:
**39.7% of reachable hosts change class between the extreme scenarios**, and
the same host can be high or low depending only on declared shelf life and
horizon. That is exactly why the dashboard states its assumptions next to every
score.

---

## 7. Test suite

```bash
docker compose run --rm tools python -m pytest tests -q
```

```
61 passed
```

The suite covers the classifier (including the `ML-DSA`/`DSA` and
`X25519MLKEM768`/`X25519` traps), the Mosca thresholds, database upserts and
error rows, OpenSSL output parsing, Tranco sampling determinism and the
dashboard's JSON safety.

---

## 8. Summary of findings

1. **The scanner is reliable on known ground truth** — 100% exact match on 20
   lab configurations, precision and recall 1.00.
2. **Hybrid post-quantum key exchange is already mainstream** — 60.3% of
   reachable top-10k domains negotiated `X25519MLKEM768`.
3. **Post-quantum authentication is not deployed** — no sampled host presented
   an ML-DSA certificate; RSA still signs 69.9% of certificates.
4. **The migration cost is bytes, not time** — hybrid TLS adds 80.9% more
   handshake bytes but 0.8% more time.
5. **ML-KEM is cheap, ML-DSA is not** — encapsulation is 8× faster than RSA
   signing, but ML-DSA signing is 3.7× slower than RSA signing and its
   signatures are 12.9× larger.
6. **Constraints scale everything equally** — halving CPU halves throughput
   for classical and post-quantum algorithms alike.
7. **Risk verdicts are assumption-dependent** — 39.7% of reachable hosts
   change class between extreme planning scenarios, while the naive rule calls
   all 100% high and therefore cannot prioritise.
