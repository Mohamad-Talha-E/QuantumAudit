# QuantumAudit: Cryptographic Inventory, Quantum-Risk Scoring, and Post-Quantum Migration Benchmarking

Mohamad Talha Ezzo (23000488), Bahaa Mohamad (23001498), Ahmad Abualrub (23001599), Omar Abuzaid (23001809)

CSCY413 — Special Topics in Cybersecurity
Group Project, Deliverable 2: Implementation, Results and Discussion
Track: Post-Quantum and Quantum-Safe Security
Instructor: Dr. Sapna Sadhwani
GitHub: https://github.com/Mohamad-Talha-E/QuantumAudit

**Abstract—** QuantumAudit is a working system for supporting post-quantum
migration planning through cryptographic inventory, transparent risk rules and
controlled performance measurements. The implementation combines a TLS metadata
scanner, a Mosca-based contextual risk scorer with a naive baseline, a
20-configuration Docker lab, a post-quantum benchmark harness and a FastAPI
dashboard. The scanner was validated against the lab and achieved a 100% exact
match on all 20 configurations, with precision and recall of 1.00 for the
post-quantum detection decision. A reproducible 100-domain sample from the top
10,000 Tranco domains found 73 reachable hosts, of which 44 (60.3%) already
negotiated the hybrid `X25519MLKEM768` group while 29 remained classical-only.
No sampled public host presented a post-quantum certificate. Benchmarking
showed that ML-KEM-768 encapsulation costs 0.0237 ms, roughly eight times faster
than RSA-2048 signing, whereas ML-DSA-65 signing costs 0.7117 ms and produces a
signature 12.9 times larger than RSA-2048. A hybrid TLS 1.3 handshake added 0.8%
in time but 80.9% in bytes over the classical handshake. Under a 0.5 CPU and
256 MB limit, throughput approximately halved for classical and post-quantum
algorithms alike. A sensitivity analysis showed that 29 of the 73 reachable
hosts (39.7%) change risk class between extreme planning scenarios, while the
naive rule classifies all 73 as high. The central finding is that handshake
metadata alone cannot prioritise migration: the declared planning assumptions
matter as much as the observed algorithms, and a tool that hides them produces
an unstable headline rather than a decision.

**Index Terms—** post-quantum cryptography, TLS, cryptographic inventory, risk
assessment, benchmarking.

---

## I. Introduction

### A. Problem Statement

Much of the traffic on today's internet is protected by public-key
cryptography. RSA, Diffie–Hellman and elliptic-curve cryptography (ECC) rely on
the difficulty of integer factorisation or discrete logarithms. With Shor's
algorithm, a sufficiently large quantum computer could solve these problems in
polynomial time, breaking the security of these systems [1]. Symmetric
encryption faces a different threat: Grover's algorithm gives a quadratic
speed-up for generic key search [2]. Describing this as halving the effective
key strength refers to an idealised query-complexity model, not a complete
estimate of attack cost. Practical AES security also depends on implementation
costs and parallelism, and NIST's current guidance continues to permit AES-128,
AES-192 and AES-256 [3].

Organisations need to prepare before a quantum computer capable of breaking
those systems exists. An attacker can already capture encrypted traffic and
store it until decryption becomes feasible. This "harvest now, decrypt later"
(HNDL) threat is especially relevant for health, financial and government
records that must remain confidential for many years [4], [5].

In August 2024, NIST published the first post-quantum standards: FIPS 203 for
ML-KEM key establishment, and FIPS 204 and FIPS 205 for ML-DSA and SLH-DSA
signatures [6]. With standards available, the practical question is no longer
*which algorithm* but *where the vulnerable cryptography is and what to migrate
first*. Answering that requires evidence from actual deployments — the
negotiated key-exchange group, certificate key type, signature algorithm and
protocol version. A handshake can supply that evidence. It cannot supply data
retention requirements or migration effort, which also determine priority.
Broad statements about quantum threats are therefore not enough to set useful
priorities [4], [5].

### B. Motivation and Relevance

Singh and Kumar [7] and Jowarder and Jahan [5] argue that organisations must
move to quantum-resistant cryptography. Their reviews explain why migration is
necessary but do not provide a repeatable process for measuring an
organisation's own systems. Without an inventory of TLS configurations and a
well-defined scoring rule, it is difficult to decide where to start.

QuantumAudit combines those tasks. It collects cryptographic information
visible in TLS handshakes, applies a rule-based risk score informed by Mosca's
inequality [4], and benchmarks classical and post-quantum algorithms. A web
dashboard presents each score with its assumptions, its reason and a suggested
next step. The goal is a prioritised list that a practitioner can act on and
argue with, rather than a single opaque risk rating.

**Research question.** To what extent can TLS handshake metadata, transparent
scenario-based risk rules and controlled performance measurements support
post-quantum migration planning?

### C. Scope

The delivered system covers five areas:

- **Inventory:** one standard TLS handshake per host for a seeded sample of 100
  domains from the Tranco research-oriented top-sites ranking [8], plus 20
  controlled lab configurations. The original plan specified 1,000 public
  domains; the reduction is a documented scope decision (§V-B and
  `DEVIATIONS.md` §5.2), and the 1,000-domain command remains available.
- **Risk scoring:** a comparison between a naive baseline that flags all
  RSA/ECC use as high risk and a contextual score based on algorithm class,
  data shelf life and migration time. The contextual model applies Mosca's
  inequality under quantum-arrival scenarios of 10, 15 and 20 years.
- **Benchmarking:** RSA-2048, ECDH P-256, X25519 and ECDSA P-256 against
  ML-KEM-768 and ML-DSA-65, measuring execution time and relevant key,
  ciphertext and signature sizes, including tests under resource constraints.
- **Handshake overhead:** hybrid X25519 + ML-KEM-768 key exchange compared with
  classical-only TLS 1.3 in a controlled lab.
- **Dashboard:** a web application presenting findings, risk scores, the reason
  for each score and a recommended migration step.

The project does not attack, decrypt or exploit third-party systems, and does
not simulate a quantum computer. Public-host measurement stayed within the
rate-limited, handshake-only approach described in §III-G.

---

## II. Literature Review

The review centres on the two papers assigned to our track, Singh and Kumar [7]
and Jowarder and Jahan [5]. Foundational cryptographic and measurement
literature connects their recommendations to the project design.

### A. Singh and Kumar on Quantum Computing and AI for Cybersecurity

Singh and Kumar review the relationship between quantum computing and
cybersecurity [7]. Three parts of their discussion are relevant. First, they
explain the threat Shor's algorithm poses to RSA and ECC and discuss
post-quantum alternatives, including lattice-based, code-based and multivariate
schemes. Second, they consider quantum random number generators and quantum key
distribution (QKD) as defensive technologies. Third, they discuss how quantum
computing and AI could support threat detection through large-scale pattern
recognition. The paper also raises ethical and regulatory concerns, including
equitable access and compliance during the transition.

The paper is broad but conceptual. It discusses possible uses of quantum
technology without providing a dataset, measurement method or tool that an
organisation could use to assess its current exposure. Its recommendation to
move towards quantum-resistant encryption therefore leaves an important
practical question open: how should an organisation identify the systems that
need attention first? The cryptography discussion focuses on public-key threats
and post-quantum alternatives; our project also examines symmetric-key
exposure. For QuantumAudit, the main gap is the absence of a practical
inventory and assessment process.

### B. Jowarder and Jahan on Threats and Mitigation

Jowarder and Jahan focus more closely on the threats to existing
cryptography [5]. They discuss Shor's algorithm against RSA and ECC, the effect
of Grover's algorithm on symmetric-key search, and vulnerabilities in QKD
systems. In the simplified key-search model they describe, a 256-bit AES key
provides roughly 128-bit security against a quantum adversary. Their proposed
mitigations include post-quantum cryptography, hybrid approaches that combine
classical and quantum-resistant algorithms, NIST standardisation, and continued
research investment. They also recommend patching, monitoring, incident-response
planning and risk-management frameworks.

Compared with Singh and Kumar [7], this paper gives more attention to how the
threats work and how a transition might be managed. Its discussion of hybrid
encryption directly informs Experiment 4. However, it does not measure the
proposed mitigations. It provides no inventory of deployed systems, no
performance comparison for migration, and no analysis of how risk assessments
change under different quantum-arrival assumptions. The uncertainty surrounding
a cryptographically relevant quantum computer (CRQC) is therefore central to
our design. Mosca's inequality makes the assumed timeline explicit, allowing us
to test how it affects migration priorities rather than relying on a single
prediction.

### C. Supporting Literature

**Foundational algorithms.** Shor [1] showed that a quantum computer can solve
integer factorisation and discrete-logarithm problems in polynomial time,
establishing the basis of the threat to RSA and ECC. Grover [2] demonstrated a
quadratic speed-up for unstructured search. This informs the discussion of
symmetric-key exposure, but practical AES security requires a separate
assessment [3].

**Risk modelling.** Mosca's inequality [4] connects the HNDL threat to
migration planning. Let X be the period for which data must remain secure, Y
the time needed to migrate, and Z the time until a CRQC becomes available. The
planning concern arises when X + Y > Z. Instead of requiring a precise
prediction of quantum arrival, the model lets us state assumptions and examine
their consequences. This is the basis of our contextual score.

**Standardisation and deployment.** NIST's 2024 standards define ML-KEM,
ML-DSA and SLH-DSA [6] and provide a reference for classifying post-quantum
algorithms. Yalamuri, Honnavalli and Eswaran [9] review pre-standardisation
options and identify lattice-based and code-based schemes as important
candidates, supporting our selection of ML-KEM and ML-DSA. von Nethen et
al. [10] discuss migration management and identify inventory and prioritisation
as practical obstacles, supporting an inventory-first approach. Liu et
al. [11] examine post-quantum cryptography in IoT settings, where limited
resources make performance particularly important, motivating our
constrained-resource experiment.

**Measurement infrastructure.** The Tranco list, developed by Le Pochat et
al. [8], is a research-oriented top-sites ranking designed to resist
manipulation, giving a documented basis for sampling domains. The Open Quantum
Safe project's liboqs library [12] supplies post-quantum implementations. In
this implementation we used the native ML-KEM and ML-DSA support in OpenSSL
3.5.7 rather than building liboqs; this is recorded in `DEVIATIONS.md` §1.3 and
does not change the comparison, because the measured algorithms are the same
NIST standards.

**Critical perspectives.** Hoefler, Häner and Troyer [13] caution against
overstating the practical prospects of quantum advantage. We therefore treat
the 10-, 15- and 20-year horizons as scenarios, not forecasts, and report how
results change between them. Renner and Wolf [14] explain that QKD security
guarantees depend on physical and device assumptions. We keep QKD outside the
benchmark, which focuses on deployable post-quantum cryptography. The GAO
report [15] presents post-quantum readiness as a wider government
risk-management issue, consistent with using the dashboard as a planning aid.

### D. Research Gaps and Project Response

Five gaps in the reviewed material shaped the project, and each now has an
implemented response and a measured result.

- **G1: Identifying systems that need migration.** Both central reviews
  recommend post-quantum cryptography but provide no measured inventory of
  vulnerable deployments. **Response:** the scanner surveyed 100 Tranco domains
  and 20 lab configurations; results in §V-A and §V-B.
- **G2: Measuring migration costs.** The reviewed discussions give no
  performance comparison for a real deployment. **Response:** E3 and E5 measure
  execution time and key, ciphertext and signature sizes for six algorithms.
- **G3: Making timeline assumptions visible.** The arrival date of a CRQC is
  uncertain. **Response:** E6 scores risk across a grid of shelf lives and
  10/15/20-year horizons and reports which classifications change.
- **G4: Testing hybrid overhead.** **Response:** E4 measures
  X25519 + ML-KEM-768 against classical TLS 1.3 on the same lab server.
- **G5: Making findings usable.** The reviews provide no practitioner-facing
  tool. **Response:** the dashboard turns results into a prioritised list with
  explanations and suggested actions.

---

## III. Methodology

### A. System Overview

QuantumAudit collects and analyses measurements rather than training a learning
system. It has five components:

1. **TLS metadata scanner** — one Python `ssl` handshake for certificate
   fields, plus one `openssl s_client` probe for the negotiated group.
2. **Risk scorer** — a classifier, a contextual Mosca rule and a naive
   baseline.
3. **Benchmark harness** — OpenSSL 3.5.7 for E3/E5 and `s_time` plus message
   accounting for E4.
4. **Docker lab** — 20 TLS servers with known configurations and a private CA.
5. **Web dashboard** — FastAPI, Jinja2 and server-side matplotlib charts.

Records are stored in a timestamped SQLite database with three tables:
`findings` (scan facts), `scores` (one verdict per host per planning scenario)
and `bench` (timings and sizes). The split matters: the design guide used one
`reason` column for two unrelated things — why a scan failed and why a host
scored high. Separating the tables also allows one scan to be scored under many
scenarios without duplicating scan data, which E6 requires.

### B. Datasets

**Field survey.** A seeded sample of 100 domains was drawn from the top 10,000
entries of the Tranco list [8] using `random.Random(413).sample`. The seed
makes the sample exactly reproducible. Each host received one standard TLS
handshake on port 443. Only handshake metadata was recorded: protocol version,
negotiated key-exchange group, certificate algorithm and key size, signature
algorithm and certificate expiry. Connections were rate-limited to one every
0.5 seconds. No application content was requested and no payload was stored.

**Lab ground truth.** An isolated Docker lab contains 20 TLS server
configurations covering RSA-2048, RSA-4096, ECDSA P-256, ECDSA P-384, Ed25519
and ML-DSA-65 certificates; TLS 1.2 and TLS 1.3; classical groups (`X25519`,
`X448`, `P-256`, `P-384`, static RSA); pure ML-KEM (`MLKEM768`); and hybrid
groups (`X25519MLKEM768`, `SecP256r1MLKEM768`). One host negotiates AES-128 to
exercise the weakened-symmetric class. Because every configuration is known,
scanner output can be compared with exact ground truth in
`lab/lab_manifest.json`.

**Scope decision.** The proposal specified 1,000 public domains. The delivered
survey uses 100. The reasons are time and rate-limiting (1,000 hosts × two
handshakes is slow), politeness (1,000 unsolicited handshakes from one host is
closer to scanning than surveying), and sufficiency (100 is enough to show the
distribution, and the seed makes it reproducible). The full run is a documented
command and is not hidden. See `DEVIATIONS.md` §5.2.

### C. Experiment Design

- **E1: Scanner accuracy.** Scan the 20 lab configurations and compare reported
  settings with known settings, field by field.
- **E2: Quantum-risk survey.** Scan the Tranco sample, apply the baseline
  exposure classification, then apply explicit shelf-life and migration-time
  assumptions in the contextual model to show how identical observations change
  classification across planning scenarios.
- **E3: Classical and post-quantum benchmarking.** Measure RSA-2048, ECDH
  P-256, X25519, ECDSA P-256, ML-KEM-768 and ML-DSA-65. Record execution times
  and relevant key, ciphertext and signature sizes.
- **E4: Hybrid handshake overhead.** Compare duration and byte count of
  classical and hybrid TLS 1.3 handshakes against lab servers that differ only
  in key-exchange group.
- **E5: Constrained-resource testing.** Repeat E3 under Docker CPU and memory
  limits intended to approximate IoT devices and small cloud instances.
- **E6: Sensitivity analysis.** Vary shelf life and quantum horizon, and record
  changes in risk level.

### D. Risk Scoring Model

**Simple baseline.** Flag every host using RSA or ECC as high risk, without
considering context. In the implemented baseline, both `vulnerable` and
`hybrid` hosts are high, because both still contain classical asymmetric
cryptography; only fully post-quantum hosts are low. This is the honest
"no context, no timeline" baseline.

**Algorithm classification.** Each observation is assigned to one of five
classes:

| Class | Evidence |
|---|---|
| `vulnerable` | classical asymmetric crypto only (RSA, ECDH, ECDSA, DHE, DSA, Ed25519, X25519, X448, P-256, P-384) |
| `hybrid` | a mix of post-quantum and classical asymmetric evidence |
| `resistant` | post-quantum everywhere (ML-KEM, ML-DSA, SLH-DSA) |
| `weakened` | weak symmetric crypto only (AES-128, 3DES, RC4, SHA-1, MD5) |
| `unknown` | insufficient evidence |

**Contextual rule.** Apply Mosca's inequality with data shelf life X, migration
time Y and quantum horizon Z:

```
safe_window = Z - Y
hybrid or resistant           -> low
X <= safe_window              -> low
X <= safe_window + 3 years    -> medium
otherwise                     -> high
unknown                       -> medium (manual review)
```

Z is tested at 10, 15 and 20 years; X at 5, 10, 15 and 25 years; Y is fixed at
3 years. Every score stores its assumptions, its reason and a migration step,
so a reader can disagree with the assumptions rather than with an unexplained
number.

### E. Evaluation Metrics

For E1 we measured per-field accuracy, whole-row exact match, and precision,
recall and F1 for the binary "is this host post-quantum protected" decision.
Our target was at least 0.80 precision and 0.80 recall. E4 reports overhead in
milliseconds and bytes. E3 and E5 report throughput and mean latency, plus key,
ciphertext and signature sizes. E2 reports the proportion of surveyed hosts in
each risk category. E6 reports the number of hosts whose verdict changes across
the scenario grid.

### F. Tools and Technologies

The implementation uses Docker, Debian 13, OpenSSL 3.5.7, Python 3.13,
`cryptography` 50.0.2, FastAPI, Uvicorn, Jinja2, matplotlib and SQLite. Tranco
[8] provides the domain list, and NIST FIPS 203/204/205 [6] are the standards
references. The image is built with a startup check that fails if OpenSSL loses
ML-KEM-768 or ML-DSA-65 support.

Two deviations from the proposed toolchain are recorded in `DEVIATIONS.md`:
liboqs was not needed because OpenSSL 3.5 provides native ML-KEM and ML-DSA
(§1.3), and pandas is installed but the analysis code uses plain Python and
matplotlib to keep the container small and fast.

### G. Ethical and Legal Considerations

The project did not attempt to attack systems or decrypt data. Public-host
measurement was limited to one standard TLS handshake per domain, with a 0.5 s
delay, no application-content requests and no stored payload. The Tranco
licence [8] and accepted Internet-measurement practice were followed. Server
experiments ran in an isolated Docker lab with no real user data.

The risk score supports migration planning; it is not a simulation of a quantum
attack or a prediction of when one will become possible. Datasets and software
are cited in line with their licences, and only systems we were authorised to
test were used, as required by the module brief and the ethical considerations
discussed by Singh and Kumar [7].

---

## IV. Team Plan and Timeline

### A. Responsibilities

Each team member led one area, with another member providing support:

- **Mohamad Talha Ezzo (23000488): Scanner and Data Engineering.** Scanner,
  cleaned features and the SQLite findings database. Supported by Bahaa.
- **Bahaa Mohamad (23001498): Risk Analytics and Scoring.** Simple and
  contextual scoring modules, score explanations and E6. Supported by Talha.
- **Ahmad Abualrub (23001599): Lab and Cryptographic Benchmarking.** Docker lab,
  benchmark scripts, tables and charts for E3–E5. Supported by Omar.
- **Omar Abuzaid (23001809): Dashboard and Documentation.** Web application and
  final report. Supported by Ahmad.
- **All members: Integration and Review.** Cross-review of code, integrated
  results and the final demonstration. GitHub commit history documents each
  member's contribution.

### B. Weeks 4 to 8

- **Week 4: Data collection and scoring rules.** Tranco survey and feature
  engineering; Mosca rules; benchmark scripts and hybrid lab server; dashboard
  connected to the live database.
- **Weeks 5 and 6: Experiments.** E1 and E2; score explanations and E6; E3 and
  E4; risk views and charts.
- **Weeks 7 and 8: Validation and delivery.** Data frozen and validated; scores
  refined; E5 and final charts; demonstration and report.

Weeks 1 to 3 produced the scanner prototype, database schema, algorithm
classes, simple scoring rule, initial lab servers, dashboard layout and report
outline. All planned phases were completed; the only scope change was the
public sample size documented in §III-B.

### C. Risks and Mitigations

The small lab sample limits how broadly results can be interpreted, so we
report confidence in the ground truth rather than extrapolating accuracy. The
field survey is labelled as a single-date snapshot. Uncertainty about quantum
timelines is handled by E6 rather than hidden behind one assumption [13]. If
public hosts rate-limit or block connections, the scanner backs off and
maintains a conservative pace. The largest technical risk in the proposal — the
`oqsprovider` build — was eliminated by using OpenSSL 3.5's native
post-quantum support (`DEVIATIONS.md` §1.3).

---

## V. Results

All numbers below were produced by this repository. Environment: Docker
29.9.2, Debian 13, OpenSSL 3.5.7, Python 3.13.5, `cryptography` 50.0.2, host
with 12 logical cores and ~7.9 GB memory. Full tables and regeneration commands
are in `results.md`.

### A. E1 — Scanner accuracy against the lab

Twenty controlled servers on ports 8443–8462 were scanned and compared field by
field with `lab/lab_manifest.json`.

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

The lab deliberately includes awkward cases: TLS 1.2, pure ML-KEM with no
classical fallback, the `SecP256r1MLKEM768` hybrid group, ML-DSA-65
certificates, Ed25519, X448 and an AES-128-only host. A perfect score therefore
means the scanner distinguishes these cases, not merely that it can reach a
server. During development the tests also exposed two real classifier bugs — a
naive substring match treated `ML-DSA` as `DSA`, and `AES128-SHA` was not
recognised as AES-128 — both fixed and covered by regression tests.

### B. E2 — Real-world TLS survey

Sample: 100 domains drawn with seed 413 from the top 10,000 Tranco entries
(1,000,000 entries downloaded). The sample is reproducible.

**Reachability.**

| Outcome | Hosts |
|---|---|
| Reachable, handshake completed | **73** |
| No DNS record (no A/AAAA) | 20 |
| Connection timeout | 4 |
| TLS connection closed before certificate | 3 |
| **Total sampled** | **100** |

The 27 failures are survey data, not scanner errors. Verified with a public
DNS-over-HTTPS resolver: several failed names (`msecnd.net`, `zooplus.net`,
`kameleoon.io`) return `NOERROR` with no A, AAAA or CNAME record — they are
registered names that do not serve a website. Tranco ranks traffic to any
subdomain, so the apex name need not be a web server. Three hosts accepted TCP
but closed before completing the handshake; these were initially recorded as
`ok` because the parser accepted the string `<NULL>` as a group. The handshake
success test was corrected to require a real cipher, and those hosts are now
correctly errors.

Adoption percentages below use **73**, the number of hosts that answered.

**Negotiated key exchange.**

| Group | Hosts | Share |
|---|---|---|
| **X25519MLKEM768** (hybrid, post-quantum) | **44** | **60.3%** |
| X25519 (classical) | 17 | 23.3% |
| P-256 (classical) | 10 | 13.7% |
| P-384 (classical) | 1 | 1.4% |
| RSA (static, no forward secrecy) | 1 | 1.4% |

**Protocol and certificate algorithms.**

| Protocol | Hosts |
|---|---|
| TLS 1.3 | 60 (82.2%) |
| TLS 1.2 | 13 (17.8%) |

| Certificate key | Hosts |
|---|---|
| RSA | 51 (69.9%) |
| EC | 22 (30.1%) |

No sampled public host used an ML-DSA certificate, which matches deployment
reality: post-quantum key exchange is being rolled out, post-quantum
authentication is not yet.

**Risk classification.**

| Model | Low | Medium | High |
|---|---|---|---|
| Naive rule (no context) | 0 | 0 | **73** |
| Contextual, default `x15_y3_z15` | **44** | 0 | **29** |

Algorithm classes: **44 hybrid**, **29 vulnerable**.

The contextual model moves 44 hosts (60.3%) from high to low because their data
does not need to stay secret longer than the safe window left after migration.
This is the central E2 result: a handshake alone cannot prioritise migration;
the planning assumptions matter as much as the algorithm. These are per-domain
observations, not verified organisation-specific priorities.

### C. E3 — Classical versus post-quantum algorithms

Measured with `openssl speed -elapsed -seconds 2`. Mean milliseconds are
`1000 / ops_per_s`.

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

**Sizes (bytes).**

| Algorithm | Public key | Private key | Ciphertext / signature |
|---|---:|---:|---:|
| ML-KEM-768 | 1,206 | 2,498 | 1,088 (ciphertext) |
| ML-DSA-65 | 1,974 | 4,098 | 3,309 (signature) |
| RSA-2048 | 294 | 1,192 | 256 (signature) |
| ECDSA P-256 | 91 | 121 | 71 (signature) |
| ECDH P-256 | 91 | 121 | — |
| X25519 | 44 | 48 | — |

ML-KEM-768 encapsulation is about eight times faster than RSA-2048 signing
(0.0237 ms versus 0.1925 ms) and produces a 1,088-byte ciphertext instead of a
256-byte signature. ML-DSA-65 signing is the slowest operation measured
(0.7117 ms) and its signature is 12.9 times larger than RSA-2048's. The
asymmetry matters for migration planning: replacing key establishment is cheap,
while replacing signatures is the expensive part.

### D. E4 — Hybrid handshake overhead

Two lab servers differ only in key-exchange group: port 8443 (X25519) and port
8447 (X25519 + ML-KEM-768). Timing used `openssl s_time -new`; byte counts sum
TLS message lengths up to the first application-data record.

| Handshake | Handshakes/sec | Mean ms | Handshake bytes |
|---|---:|---:|---:|
| TLS 1.3 classical (X25519) | 2,501 | 0.400 | 2,207 |
| TLS 1.3 hybrid (X25519+ML-KEM-768) | 2,482 | 0.403 | 3,993 |

| Delta | Value |
|---|---|
| Time | **+0.003 ms** per handshake (+0.8%) |
| Bytes | **+1,786 bytes** per handshake (+80.9%) |

The hybrid transition is almost free in time and expensive in bytes. That is
the expected trade-off: one extra KEM ciphertext and public key, no extra round
trips. The result supports the deployment pattern observed in E2, where hybrid
key exchange is already widespread on public hosts.

### E5 — Constrained resources

The E3 harness was repeated with `--cpus=0.5 --memory=256m`.

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

Halving the CPU halves throughput almost exactly for both classical and
post-quantum algorithms. No algorithm has a pathological behaviour under
constraint, and ML-KEM-768 encapsulation still costs only 0.048 ms on half a
core. An earlier E5 run produced numbers identical to E3 because `openssl speed`
divides by CPU time; adding `-elapsed` fixed the measurement
(`DEVIATIONS.md` §1.6). Reporting the artefact would have been a false result.

### F. E6 — Sensitivity analysis

Migration time is fixed at 3 years. Shelf life varies over 5/10/15/25 years;
quantum horizon over 10/15/20 years.

**Lab run (20 hosts).**

| Metric | Value |
|---|---|
| Hosts scored | 20 |
| Algorithm classes | 13 vulnerable, 7 hybrid |
| Naive rule: high | 20 (100%) |
| Contextual, `x15_y3_z15` | 13 high, 7 low |
| Verdict changes, `x5_z20` → `x25_z10` | **13** |

**Tranco run (73 reachable hosts).**

| Metric | Value |
|---|---|
| Hosts scored | 73 |
| Algorithm classes | 44 hybrid, 29 vulnerable |
| Naive rule: high | 73 (100%) |
| Contextual, `x15_y3_z15` | 29 high, 44 low |
| Verdict changes, `x5_z20` → `x25_z10` | **29** |

**Full grid — Tranco run.**

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

The 44 hybrid hosts are always low because their key exchange is already
post-quantum. The 29 vulnerable hosts move between low, medium and high as the
assumptions change. A single "high risk" headline is therefore unstable:
**39.7% of reachable hosts change class between the extreme scenarios**, and
the same host can be high or low depending only on declared shelf life and
horizon. The naive rule, by contrast, returns the same answer for every
scenario and therefore cannot prioritise at all.

### G. Test suite

```
docker compose run --rm tools python -m pytest tests -q
61 passed
```

The suite covers the classifier (including the `ML-DSA`/`DSA` and
`X25519MLKEM768`/`X25519` traps), the Mosca thresholds, database upserts and
error rows, OpenSSL output parsing, Tranco sampling determinism and the
dashboard's JSON safety. Tests found real defects during development, including
a classifier that could not recognise `AES128-SHA`, a parser that accepted
`<NULL>` as a group name, and a dashboard payload that was not JSON-native.

---

## VI. Discussion and Limitations

### A. Interpretation

Three findings stand out.

**Hybrid key exchange has arrived; post-quantum authentication has not.** Of 73
reachable hosts, 44 negotiated a hybrid post-quantum group, but none presented a
post-quantum certificate. This matches the deployment order predicted in the
literature: key establishment is upgraded first because it is cheap and
transparent, while signatures require certificate-authority and client support.
A migration plan that focuses only on certificates would therefore miss the
area where progress is already possible.

**The cost of hybrid key exchange is bytes, not time.** E4 measured +0.8% time
and +80.9% bytes. This is a favourable trade: latency and CPU are largely
unchanged, and the extra bytes are well within normal TLS record sizes. The
result supports the observed public deployment.

**ML-KEM is cheap; ML-DSA is the bottleneck.** ML-KEM encapsulation was about
eight times faster than RSA signing, but ML-DSA signing was 3.7 times slower
than RSA signing with a signature 12.9 times larger. For constrained devices,
the signature side is where engineering effort is needed. E5 showed that
constraints scale all algorithms roughly equally, so the relative gap persists
rather than being an artefact of the machine.

**Risk verdicts depend on assumptions.** E6 is the most important result for
practice. The same 73 hosts produce 29 high-risk verdicts or 0, depending on
shelf life and horizon. A tool that reports one number without its assumptions
is not giving a decision; it is giving a headline. QuantumAudit stores the
assumptions, the reason and a next step with every score.

### B. Comparison with the proposal

The proposal anticipated all six experiments and the main design decisions held.
Three changes were necessary and are documented in `DEVIATIONS.md`:

1. **Public sample size.** 100 domains instead of 1,000, for time, politeness
   and sufficiency reasons (§III-B).
2. **Toolchain.** Native OpenSSL 3.5 instead of liboqs, which removed the
   highest-risk build step without changing the measured standards.
3. **Measurement method.** E4 uses `s_time` and TLS message accounting instead
   of `curl`, because `curl` measures the HTTP body, not the handshake, and
   cannot answer how many bytes the key exchange adds.

### C. Limitations

1. **TLS 1.2 group detection is best-effort.** When a server omits the
   temporary-key line, the group is inferred from the cipher suite
   (`ECDHE`/`DHE`/`RSA`). This is enough for the risk decision but is not a
   curve name.
2. **`sig_alg` on lab ML-DSA certificates reports RSA.** The lab CA signs with
   RSA, so the certificate signature algorithm is RSA even though the subject
   key is ML-DSA. The scanner reports both separately, and the classifier uses
   the subject key, which is the correct choice for "what breaks under a
   quantum computer".
3. **The naive rule is deliberately crude.** That is its purpose as a baseline.
4. **The public survey is a snapshot.** Tranco membership and server
   configuration change. The seed makes the sample reproducible, not the
   results.
5. **Timings are hardware-specific.** E3/E4/E5 describe this machine and should
   be compared within the run, not against published benchmarks.
6. **The score is illustrative.** A per-domain observation is not a verified
   organisation-specific priority; real planning needs asset ownership,
   application dependencies and data classification.

---

## VII. Conclusion

QuantumAudit set out to answer whether TLS handshake metadata, transparent
scenario-based rules and controlled measurements can support post-quantum
migration planning. The implementation shows that they can, with two conditions.

First, the inventory must be trustworthy. Against 20 known lab configurations
the scanner achieved a 100% exact match and perfect precision and recall, which
means the observations that feed the score are not guesswork. On real hosts it
found that 60.3% of reachable top-10k domains already use hybrid post-quantum
key exchange while none use post-quantum certificates — a clear, actionable
picture of where deployment stands.

Second, the scoring must expose its assumptions. The same observations produce
29 high-risk verdicts or none depending on declared shelf life and horizon,
while the naive rule labels every host high and therefore cannot prioritise.
Making X, Y and Z explicit turns an unstable headline into a defensible planning
conversation.

The performance results complete the picture. Hybrid key exchange costs almost
nothing in time and 80.9% more bytes; ML-KEM is cheap; ML-DSA is the expensive
part; and constrained hardware slows classical and post-quantum algorithms
equally. Together these results suggest a practical migration order: adopt
hybrid key exchange first because it is cheap and already deployed, plan
carefully for signature migration, and state the data-retention assumptions
that justify each priority.

Future work should expand the public sample to the full 1,000 domains, add
certificate-chain and client-compatibility checks, and let practitioners enter
their own shelf life and migration estimates through the dashboard rather than
editing command-line defaults.

---

## References

[1] P. W. Shor, "Polynomial-time algorithms for prime factorization and discrete logarithms on a quantum computer," *SIAM Journal on Computing*, vol. 26, no. 5, pp. 1484–1509, 1997.

[2] L. K. Grover, "A fast quantum mechanical algorithm for database search," in *Proc. 28th Annual ACM Symposium on Theory of Computing (STOC '96)*, 1996, pp. 212–219.

[3] National Institute of Standards and Technology, "Post-Quantum Cryptography FAQs," question on AES key lengths, updated Aug. 5, 2026. [Online]. Available: https://csrc.nist.gov/Projects/post-quantum-cryptography/faqs. Accessed: Oct. 18, 2026.

[4] M. Mosca, "Cybersecurity in an era with quantum computers: will we be ready?" *IEEE Security & Privacy*, vol. 16, no. 5, pp. 38–41, 2018.

[5] R. A. Jowarder and S. Jahan, "Quantum computing in cyber security: Emerging threats, mitigation strategies, and future implications for data protection," *World Journal of Advanced Engineering Technology and Sciences*, vol. 13, no. 01, pp. 330–339, 2024.

[6] National Institute of Standards and Technology, FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard; FIPS 204: Module-Lattice-Based Digital Signature Standard; FIPS 205: Stateless Hash-Based Digital Signature Standard, 2024. [Online]. Available: https://csrc.nist.gov/projects/post-quantum-cryptography

[7] S. Singh and D. Kumar, "Enhancing cyber security using quantum computing and artificial intelligence: A review," *International Journal of Advanced Research in Science, Communication and Technology*, vol. 4, no. 3, pp. 4–11, 2024.

[8] V. Le Pochat, T. Van Goethem, S. Tajalizadehkhoob, M. Korczyński and W. Joosen, "Tranco: A research-oriented top sites ranking hardened against manipulation," in *Proc. Network and Distributed System Security Symposium (NDSS)*, 2019.

[9] G. Yalamuri, P. Honnavalli and S. Eswaran, "A review of the present cryptographic arsenal to deal with post-quantum threats," *Procedia Computer Science*, vol. 215, pp. 834–845, 2022, doi: 10.1016/j.procs.2022.12.086.

[10] N. von Nethen, A. Wiesmaier, N. Alnahawi and J. Henrich, "PMMP — PQC Migration Management Process," arXiv:2301.04491, 2023.

[11] T. Liu, G. Ramachandran and R. Jurdak, "Post-Quantum Cryptography for Internet of Things: A Survey on Performance and Optimization," arXiv:2401.17538, 2024.

[12] Open Quantum Safe Project, liboqs [Software]. [Online]. Available: https://openquantumsafe.org

[13] T. Hoefler, T. Häner and M. Troyer, "Disentangling Hype from Practicality: On Realistically Achieving Quantum Advantage," *Communications of the ACM*, vol. 66, no. 5, pp. 82–87, 2023, doi: 10.1145/3571725.

[14] R. Renner and R. Wolf, "Quantum advantage in cryptography," *AIAA Journal*, vol. 61, no. 5, pp. 1895–1910, 2023, doi: 10.2514/1.J062267.

[15] U. S. Government Accountability Office, "Science & Tech Spotlight: Securing Data for a Post-Quantum World," GAO-23-106559, 2023.

---

## Appendix A — Deviations and Reproducibility

Every difference between this implementation and the design guide is recorded
in [`DEVIATIONS.md`](DEVIATIONS.md), including corrected OpenSSL algorithm names,
the schema split, the `-elapsed` timing fix, the lab certificate-generator fix,
the E2 scope decision, the E4 measurement method and the classifier
corrections. Every measured number in this report is reproduced by the commands
in [`results.md`](results.md).

## Appendix B — AI-use disclosure

AI-assisted tools were used to refine wording, improve clarity and presentation,
and support review of technical explanations and citations. All code, commands,
measurements and results were produced and verified by the project team.
