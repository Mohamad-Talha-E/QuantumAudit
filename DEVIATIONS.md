# Deviations from the design guide

This file records every place where the implementation differs from
`QuantumAudit_Project_Context.md`, and why. The rule was simple: **never fake
a number, and never hide a change.** Where the guide could not work as
written, the replacement is explained here.

Legend: **Guide** = what the design document specified, **Built** = what this
repository actually does, **Why** = the reason for the change.

---

## 1. Runtime and toolchain

### 1.1 Docker-only runtime

- **Guide:** install OpenSSL 3.x and Python packages on the host.
- **Built:** everything runs in the `quantumaudit/tools` container.
- **Why:** the development host is Windows. It has no `openssl` on `PATH`, and
  Python's bundled OpenSSL (3.0.x) cannot negotiate ML-KEM or ML-DSA. A
  container also makes the result reproducible for the marker.

### 1.2 Debian 13 instead of Alpine

- **Guide:** Alpine was implied (small image).
- **Built:** `debian:13-slim`.
- **Why:** two reasons. (a) Debian 13 ships OpenSSL **3.5.7** with ML-KEM and
  ML-DSA built in. (b) It uses glibc, so `pandas` and `matplotlib` install
  from pre-built wheels instead of compiling for ~15 minutes.

### 1.3 No `oqsprovider`

- **Guide:** build OpenSSL 3.0 plus the `oqsprovider` plugin to get
  post-quantum algorithms.
- **Built:** no plugin at all. Native OpenSSL 3.5.
- **Why:** the plugin build was the biggest risk in the plan (version
  matching, C toolchain, long builds). OpenSSL 3.5 already provides
  `ML-KEM-768`, `ML-DSA-65` and the hybrid TLS groups. Removing the plugin
  removed the risk entirely.

### 1.4 Correct OpenSSL algorithm names

- **Guide:** `openssl speed mlkem768`, `openssl speed mldsa65`.
- **Built:** `openssl speed ML-KEM-768`, `openssl speed ML-DSA-65`.
- **Why:** the lower-case, hyphen-free names are rejected
  (`speed: Unknown algorithm mlkem768`). The hyphens are required.

### 1.5 Correct `pkeyutl` flags

- **Guide:** `-encapsulate` / `-decapsulate`.
- **Built:** `-encap` / `-decap`.
- **Why:** the long spellings do not exist in OpenSSL 3.5
  (`pkeyutl: Unknown option: -encapsulate`).

### 1.6 `openssl speed -elapsed`

- **Guide:** `openssl speed -seconds N <alg>`.
- **Built:** `openssl speed -elapsed -seconds N <alg>`.
- **Why:** `speed` divides by **CPU time** by default. Inside a CPU-throttled
  container the process is simply descheduled, so throughput looks identical
  to an unthrottled run. The first E5 attempt produced numbers equal to E3
  to the last digit — a measurement artefact, not a result. `-elapsed` uses
  wall-clock time, which is what a real constrained device experiences.

---

## 2. Data model

### 2.1 Three tables instead of one

- **Guide:** one table with a `reason` column.
- **Built:** `findings` (scan facts), `scores` (one verdict per host per
  planning scenario), `bench` (timings and sizes).
- **Why:** the guide used `reason` for two unrelated things — *why a scan
  failed* and *why a host scored high*. That is exactly the "schema drift"
  the guide itself warns about. Splitting the tables also lets one scan be
  scored under many scenarios (needed for E6) without duplicating scan data.

### 2.2 Error rows are stored, not crashed on

- **Guide:** an insert that left keys out of the parameter dictionary on the
  error path.
- **Built:** every column is supplied explicitly; a failed scan is a normal
  row with `status = 'error'` and an `error` message.
- **Why:** the guide's insert raised `ProgrammingError` on precisely the
  failed scans it told us to keep. Failed hosts matter: a host that refuses
  a handshake is itself a finding.

### 2.3 Re-scans update instead of duplicating

- **Guide:** plain `INSERT`.
- **Built:** `ON CONFLICT (run_id, host, port) DO UPDATE`.
- **Why:** after fixing a scanner bug, re-running the experiment must refresh
  the stored rows. Otherwise old, wrong rows silently survive.

### 2.4 `hybrid_flag` has a narrow meaning

- **Built:** `hybrid_flag = 1` means the **negotiated key-exchange group**
  contains ML-KEM (for example `X25519MLKEM768`).
- **Note:** the classifier's `hybrid` class is broader: *any* mix of
  post-quantum and classical asymmetric evidence, including an ML-DSA
  certificate on a classical X25519 exchange. The two numbers therefore
  differ (6 vs 7 on the lab). Both are reported and labelled.

---

## 3. Scanner

### 3.1 Two handshakes per host

- **Guide:** one Python `ssl` handshake.
- **Built:** a Python `ssl` handshake for certificate fields, then an
  `openssl s_client` probe for the negotiated group.
- **Why:** Python's `ssl` module cannot report the key-exchange group at all.
  The probe is also a fallback: CPython's bundled OpenSSL 3.0 cannot negotiate
  ML-KEM-only servers or ML-DSA certificates, so those hosts would otherwise
  be recorded as errors. The `openssl` 3.5 CLI can, and its output supplies
  the protocol, cipher and certificate.

### 3.2 Lab profile trusts the lab CA

- **Guide:** `ssl.create_default_context()` unconditionally.
- **Built:** `--profile lab` trusts `lab/certs/ca.pem`.
- **Why:** lab servers use a private CA. The guide's version failed
  certificate verification on every lab host, so E1 could not run at all.

### 3.3 TLS 1.2 group parsing

- **Built:** parses `Peer Temp Key` **and** `Server Temp Key`, strips the
  method label (`ECDH`), and maps `prime256v1` → `P-256`.
- **Why:** TLS 1.3 prints `Negotiated TLS1.3 group: ...`; TLS 1.2 prints
  `Peer Temp Key: ECDH, prime256v1, 256 bits`. A failed handshake prints
  `<NULL>`, which is treated as `unknown`, not as a group name.

### 3.4 Default group list

- **Built:** offers `X25519MLKEM768`, `SecP256r1MLKEM768`,
  `SecP384r1MLKEM1024`, `MLKEM768`, then classical fallbacks.
- **Why:** some servers accept only the `SecP*MLKEM*` variants. Without them,
  the lab's port 8461 failed to negotiate and E1 lost a host.

### 3.5 Fallback when no group line is printed

- **Built:** `infer_from_cipher()` derives `ECDHE` / `DHE` / `RSA` from the
  cipher suite name.
- **Why:** some TLS 1.2 servers omit the temporary-key line. The cipher suite
  still tells us whether the exchange is ephemeral, which is enough for the
  vulnerability decision.

### 3.6 Certificate algorithm fallback

- **Built:** if `cryptography` cannot parse a post-quantum public key, the
  scanner records the algorithm OID instead of dropping the certificate.
- **Why:** a scanner must degrade, not crash. In practice
  `cryptography` 50.0.2 parses ML-DSA certificates, but the fallback keeps
  older versions usable.

---

## 4. Lab

### 4.1 Certificate generator bug fixed

- **Guide:** `alg=${spec#*:}` to split `"rsa:2048"`.
- **Built:** explicit `make_rsa` / `make_ec` / `make_ed25519` / `make_mldsa65`
  functions.
- **Why:** the guide's expression returns `"rsa:2048"`, not `"rsa"`, so the
  RSA branch was never taken and the script tried to build an elliptic curve
  called `"P-2048"`. It failed on the first iteration.

### 4.2 Twenty servers, six certificate types

- **Built:** 20 servers on ports 8443–8462: RSA-2048, RSA-4096, EC P-256,
  EC P-384, Ed25519, ML-DSA-65; TLS 1.2 and 1.3; classical, pure ML-KEM and
  hybrid groups; one AES-128 host.
- **Why:** the lab needs enough variety to prove the scanner distinguishes
  cases, not just that it can reach a server. ML-DSA certificates were added
  because OpenSSL 3.5 supports them and no other part of the project
  exercises post-quantum *authentication*.

### 4.3 `DNS:lab` added to the SAN

- **Built:** certificates include `DNS:lab`.
- **Why:** the scanner runs in a separate container and reaches the lab by
  the Compose service name `lab`. Without the SAN, hostname verification
  fails.

---

## 5. Experiments

### 5.1 E1 acceptance criteria

- **Guide:** none stated.
- **Built:** the module brief's target — precision and recall ≥ 0.80 for the
  "is this host post-quantum protected" decision, plus per-field accuracy and
  exact-match rate.
- **Why:** a single accuracy number hides which field failed. The extra
  metrics make failures diagnosable.

### 5.2 E2 scope: 100 domains, not 1,000

- **Guide:** scan the top 1,000 Tranco domains.
- **Built:** lab-first, then a **seeded 100-domain sample** from the top
  10,000. The 1,000-domain command is documented and works.
- **Why:** (a) time and rate-limiting — 1,000 hosts × two handshakes is slow;
  (b) politeness — 1,000 unsolicited handshakes from one host is closer to
  scanning than surveying; (c) 100 is enough to show the distribution, and
  the seed makes it exactly reproducible. This is a scope decision, recorded
  here rather than hidden.
- **Command for the full run:**
  `python -m scanner.cli scan-tranco --n 1000 --run-id e2-tranco-1000`

### 5.3 E2 sampling pool

- **Built:** sample from the top 10,000, not the full million.
- **Why:** the project is about sites people actually use. Sampling the full
  million would mostly measure parked domains and CDN edges.

### 5.4 E4 measurement method

- **Guide:** `curl -w '%{size_download}'` for bytes.
- **Built:** `openssl s_time` for handshake rate, and `openssl s_client -msg`
  summing TLS message lengths up to the first application-data record.
- **Why:** `curl` measures the HTTP **body**, not the TLS handshake. It cannot
  answer "how many bytes does the hybrid key exchange add?". `s_time` also
  amortises process startup across thousands of handshakes, whereas timing
  individual `s_client` calls mostly measures process creation.

### 5.5 E5 resource limits

- **Built:** `--cpus=0.5 --memory=256m`, with `-elapsed` timing.
- **Why:** the guide named the experiment but not the limits. 0.5 CPU and
  256 MB approximate a small embedded device or a busy shared host.

### 5.6 E6 sensitivity design

- **Guide:** a single scenario, and a mock that "flips" verdicts.
- **Built:** a grid of shelf lives (5/10/15/25 years) × quantum horizons
  (10/15/20 years), with migration fixed at 3 years. The headline is the
  number of hosts whose verdict changes between the most optimistic and most
  pessimistic corner.
- **Why:** the guide's own Step 4 is self-contradictory. Its mock host is
  classified `hybrid`, which the scoring rule always maps to `low`, so the
  verdict can never flip. The grid makes the sensitivity claim measurable.

### 5.7 Naive baseline definition

- **Built:** the naive rule marks **both** `vulnerable` and `hybrid` hosts as
  high risk, because both still contain classical asymmetric cryptography.
  Only fully post-quantum (`resistant`) hosts are low.
- **Why:** this is the honest "no context, no timeline" baseline. It makes the
  point of the project visible: on the lab, the naive rule calls 20/20 hosts
  high, while the contextual model calls 7/20 low because their data does not
  need to stay secret long enough to matter.

---

## 6. Classifier corrections

These were bugs in the guide's pattern matching. Each has a regression test in
`tests/test_rules.py`.

1. **Underscores.** Real cipher names are `TLS_AES_128_GCM_SHA256`, but the
   guide searched for `AES-128`. The `weakened` class was unreachable. The
   classifier now normalises `_` → `-`.
2. **`ML-DSA` contains `DSA`.** A naive search labelled post-quantum
   certificates as classical. Post-quantum tokens are now stripped before
   classical tokens are matched.
3. **`X25519MLKEM768` contains `X25519`.** This is intentional in a hybrid
   group, so the host is classified `hybrid`, not `vulnerable`.
4. **`AES128-SHA`.** TLS 1.2 names omit the hyphen. The pattern is now
   `AES-?128`.
5. **`DES-CBC3`.** The real OpenSSL name for 3DES suites.

---

## 7. Dashboard

- **Guide:** a FastAPI dashboard, unspecified.
- **Built:** a single-page dashboard with run and scenario selectors, KPI
  cards, four generated charts, and a findings table sorted high-risk first.
  Every API response is JSON-native (verified by a test that runs the payload
  through `json.dumps`).
- **Why:** the guide's sample endpoint returned SQLite `Row` objects, which
  FastAPI cannot serialise. Charts are generated server-side with matplotlib
  so the page needs no JavaScript charting library.

---

## 8. Project hygiene

### 8.1 Git identity

- **Built:** commits use the author's real name and email rather than the
  GitHub handle.
- **Why:** the report is an academic submission; the real name is the correct
  author identity. It is one command to change.

### 8.2 Branch

- **Built:** work is committed on `build/full-system`, not `main`.
- **Why:** teammates may push their own branches; `main` is left alone.

### 8.3 Reproducible inputs are not committed

- **Built:** `data/*.db`, `data/*.csv`, `lab/certs/`, `lab/servers/`,
  `lab/logs/` and generated charts are gitignored.
- **Why:** they are regenerated by the documented commands. Committing them
  would bloat the repository and invite stale data.

---

## Known limitations

These are honest limits of the result, not implementation choices.

1. **TLS 1.2 group detection is best-effort.** When a server omits the
   temporary-key line, the group is inferred from the cipher suite
   (`ECDHE`/`DHE`/`RSA`), which is enough for the risk decision but is not a
   curve name.
2. **`sig_alg` on lab ML-DSA certificates reports RSA.** The lab CA signs
   with RSA, so the certificate's *signature* algorithm is RSA even though the
   *subject key* is ML-DSA. The scanner reports both separately; the
   classifier uses the subject key, which is the correct choice for
   "what breaks under a quantum computer".
3. **The naive rule is deliberately crude.** That is its purpose as a
   baseline.
4. **Real-world scans are a snapshot.** Tranco membership and server
   configuration change; the seed makes the sample reproducible, not the
   results.
5. **Handshake timing is hardware-specific.** E3/E4/E5 numbers describe this
   machine (12 logical cores, containerised) and should be compared within
   the run, not against published benchmarks.
