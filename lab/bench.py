"""E3 / E5 -- classical vs post-quantum benchmark harness.

Why this file replaces the guide's version:

* The guide's algorithm names were ``mlkem768`` / ``mldsa65``. ``openssl
  speed`` rejects those; the correct names are ``ML-KEM-768`` and
  ``ML-DSA-65``.
* Its per-operation loop was ``pass  # TODO``, so it never recorded a number.
* It promised key, ciphertext and signature sizes but never measured them.

Timings come from ``openssl speed`` (in-process, so no process-spawn
overhead). Sizes are measured once per algorithm with the CLI and stored in
the same ``bench`` table.

E5 re-runs exactly this script inside a CPU- and memory-limited container.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
import tempfile

from scanner.db import DEFAULT_DB, init_db

FLOAT = re.compile(r"\d+\.\d+")

#: label, openssl speed argument, line pattern, operations in column order
SPECS = [
    ("RSA-2048", "rsa2048", r"rsa2048", ["keygen", "sign", "verify"]),
    ("ECDH P-256", "ecdhp256", r"ecdh \(nistp256\)", ["derive"]),
    ("X25519", "ecdhx25519", r"ecdh \(x25519\)", ["derive"]),
    ("ECDSA P-256", "ecdsap256", r"ecdsa \(nistp256\)", ["sign", "verify"]),
    ("ML-KEM-768", "ML-KEM-768", r"ML-KEM-768", ["keygen", "encaps", "decaps"]),
    ("ML-DSA-65", "ML-DSA-65", r"ML-DSA-65", ["keygen", "sign", "verify"]),
]


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, **kwargs)


def _size(path: str) -> int:
    return os.path.getsize(path)


def run_speed(arg: str, seconds: int) -> str:
    # ``-elapsed`` makes the divisor wall-clock time instead of CPU time.
    # Without it, a CPU-throttled container reports the same throughput as an
    # unthrottled one, because the process simply gets descheduled -- which
    # would make E5 meaningless.
    result = subprocess.run(
        ["openssl", "speed", "-elapsed", "-seconds", str(seconds), arg],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout + result.stderr


def parse_rates(output: str, pattern: str, operations: list[str]) -> dict:
    """Pull the operations-per-second columns out of one ``speed`` line.

    ``openssl speed`` prints per-op seconds and per-op rates. The seconds are
    rounded to four decimals (often ``0.0000``), so the rates are the reliable
    figure; milliseconds are derived from them.
    """
    regex = re.compile(pattern, re.IGNORECASE)
    match = None
    for line in output.splitlines():
        if regex.search(line) and len(FLOAT.findall(line)) >= len(operations):
            # Keep the last complete data line: OpenSSL sometimes prints a
            # header *after* the first result row, so the first match can be
            # a partial or out-of-order line.
            match = line
    if match is None:
        return {}

    numbers = [float(value) for value in FLOAT.findall(match)]
    rates = numbers[-len(operations):]
    return {
        op: {
            "ops_per_s": rate,
            "mean_ms": (1000.0 / rate) if rate else None,
        }
        for op, rate in zip(operations, rates)
    }


def measure_sizes() -> dict[str, dict[str, int]]:
    """Measure key, ciphertext and signature sizes in bytes."""
    sizes: dict[str, dict[str, int]] = {}

    with tempfile.TemporaryDirectory() as work:
        message = os.path.join(work, "msg.bin")
        with open(message, "wb") as handle:
            handle.write(b"QuantumAudit benchmark message")

        def der(key: str, public: bool, name: str) -> str:
            out = os.path.join(work, name)
            cmd = ["openssl", "pkey", "-in", key]
            if public:
                cmd.append("-pubout")
            cmd += ["-outform", "DER", "-out", out]
            _run(cmd)
            return out

        # --- ML-KEM-768 -------------------------------------------------
        kem = os.path.join(work, "kem.pem")
        _run(["openssl", "genpkey", "-algorithm", "ML-KEM-768", "-out", kem])
        kem_pub = der(kem, True, "kem_pub.der")
        kem_priv = der(kem, False, "kem_priv.der")
        kem_pub_pem = os.path.join(work, "kem_pub.pem")
        _run(["openssl", "pkey", "-in", kem, "-pubout", "-out", kem_pub_pem])
        ciphertext = os.path.join(work, "kem_ct.bin")
        secret = os.path.join(work, "kem_ss.bin")
        _run([
            "openssl", "pkeyutl", "-encap", "-inkey", kem_pub_pem,
            "-out", ciphertext, "-secret", secret,
        ])
        sizes["ML-KEM-768"] = {
            "public_key": _size(kem_pub),
            "private_key": _size(kem_priv),
            "ciphertext": _size(ciphertext),
            "shared_secret": _size(secret),
        }

        # --- ML-DSA-65 --------------------------------------------------
        dsa = os.path.join(work, "dsa.pem")
        _run(["openssl", "genpkey", "-algorithm", "ML-DSA-65", "-out", dsa])
        dsa_pub = der(dsa, True, "dsa_pub.der")
        dsa_priv = der(dsa, False, "dsa_priv.der")
        dsa_sig = os.path.join(work, "dsa_sig.bin")
        _run([
            "openssl", "pkeyutl", "-sign", "-inkey", dsa, "-rawin",
            "-in", message, "-out", dsa_sig,
        ])
        sizes["ML-DSA-65"] = {
            "public_key": _size(dsa_pub),
            "private_key": _size(dsa_priv),
            "signature": _size(dsa_sig),
        }

        # --- RSA-2048 ---------------------------------------------------
        rsa = os.path.join(work, "rsa.pem")
        _run([
            "openssl", "genpkey", "-algorithm", "RSA",
            "-pkeyopt", "rsa_keygen_bits:2048", "-out", rsa,
        ])
        rsa_pub = der(rsa, True, "rsa_pub.der")
        rsa_priv = der(rsa, False, "rsa_priv.der")
        rsa_sig = os.path.join(work, "rsa_sig.bin")
        _run([
            "openssl", "dgst", "-sha256", "-sign", rsa,
            "-out", rsa_sig, message,
        ])
        sizes["RSA-2048"] = {
            "public_key": _size(rsa_pub),
            "private_key": _size(rsa_priv),
            "signature": _size(rsa_sig),
        }

        # --- ECDSA / ECDH P-256 ----------------------------------------
        ec = os.path.join(work, "ec.pem")
        _run([
            "openssl", "genpkey", "-algorithm", "EC",
            "-pkeyopt", "ec_paramgen_curve:P-256", "-out", ec,
        ])
        ec_pub = der(ec, True, "ec_pub.der")
        ec_priv = der(ec, False, "ec_priv.der")
        ec_sig = os.path.join(work, "ec_sig.bin")
        _run(["openssl", "dgst", "-sha256", "-sign", ec, "-out", ec_sig, message])
        sizes["ECDSA P-256"] = {
            "public_key": _size(ec_pub),
            "private_key": _size(ec_priv),
            "signature": _size(ec_sig),
        }
        sizes["ECDH P-256"] = {
            "public_key": _size(ec_pub),
            "private_key": _size(ec_priv),
        }

        # --- X25519 -----------------------------------------------------
        x = os.path.join(work, "x25519.pem")
        _run(["openssl", "genpkey", "-algorithm", "X25519", "-out", x])
        x_pub = der(x, True, "x_pub.der")
        x_priv = der(x, False, "x_priv.der")
        sizes["X25519"] = {
            "public_key": _size(x_pub),
            "private_key": _size(x_priv),
        }

    return sizes


def store(rows: list[dict], sizes: dict, db: str, run_id: str, constrained: bool) -> None:
    conn = init_db(db)
    stamp = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    for row in rows:
        conn.execute(
            "INSERT INTO bench (run_id, algo, op, ops_per_s, mean_ms, bytes,"
            " constrained, ts) VALUES (?, ?, ?, ?, ?, NULL, ?, ?)",
            (
                run_id, row["algo"], row["op"], row["ops_per_s"],
                row["mean_ms"], int(constrained), stamp,
            ),
        )
    for algo, fields in sizes.items():
        for name, size in fields.items():
            conn.execute(
                "INSERT INTO bench (run_id, algo, op, ops_per_s, mean_ms, bytes,"
                " constrained, ts) VALUES (?, ?, ?, NULL, NULL, ?, ?, ?)",
                (run_id, algo, name, size, int(constrained), stamp),
            )
    conn.commit()
    conn.close()


def to_markdown(rows: list[dict], sizes: dict, constrained: bool) -> str:
    title = "E5 -- constrained resources" if constrained else "E3 -- algorithm benchmark"
    lines = [f"### {title}", ""]
    if constrained:
        lines.append("Run with `--cpus=0.5 --memory=256m` to emulate a small device.")
        lines.append("")

    lines += ["| algorithm | operation | ops/sec | mean ms |", "|---|---|---|---|"]
    for row in rows:
        mean = f"{row['mean_ms']:.4f}" if row["mean_ms"] else "n/a"
        lines.append(
            f"| {row['algo']} | {row['op']} | {row['ops_per_s']:,.0f} | {mean} |"
        )

    lines += ["", "| algorithm | field | bytes |", "|---|---|---|"]
    for algo, fields in sizes.items():
        for name, size in fields.items():
            lines.append(f"| {algo} | {name} | {size:,} |")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="E3/E5 benchmark harness")
    parser.add_argument("--seconds", type=int, default=2)
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--run-id", default="e3-bench")
    parser.add_argument("--constrained", action="store_true")
    parser.add_argument("--skip-sizes", action="store_true")
    parser.add_argument("--markdown-out", default="data/bench_report.md")
    args = parser.parse_args()

    rows: list[dict] = []
    for label, arg, pattern, operations in SPECS:
        output = run_speed(arg, args.seconds)
        rates = parse_rates(output, pattern, operations)
        if not rates:
            print(f"WARNING: could not parse {label}")
            continue
        for op, values in rates.items():
            rows.append({"algo": label, "op": op, **values})
        print(f"{label}: " + ", ".join(
            f"{op} {values['ops_per_s']:,.0f}/s" for op, values in rates.items()
        ))

    sizes = {} if args.skip_sizes else measure_sizes()
    store(rows, sizes, args.db, args.run_id, args.constrained)

    markdown = to_markdown(rows, sizes, args.constrained)
    with open(args.markdown_out, "w", encoding="utf-8") as handle:
        handle.write(markdown + "\n")
    print()
    print(markdown)


if __name__ == "__main__":
    main()
