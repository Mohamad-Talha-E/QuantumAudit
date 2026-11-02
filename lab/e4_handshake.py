"""E4 -- hybrid handshake overhead.

Compares a classical TLS 1.3 handshake (X25519) with a hybrid one
(X25519 + ML-KEM-768) against two lab servers that differ only in their
key-exchange group.

Two measurements per side:

* **time** -- ``openssl s_time`` performs thousands of handshakes in one
  process, so process-spawn overhead is amortised away. This is much more
  honest than timing individual ``s_client`` calls.
* **bytes** -- ``openssl s_client -msg`` prints every TLS message with its
  length; we add up the handshake messages before application data starts.

The guide suggested ``curl -w %{size_download}`` for byte counts, which
measures the HTTP body, not the handshake.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess

from scanner.db import DEFAULT_DB, init_db

CONNECTIONS = re.compile(
    r"(\d+) connections in ([\d.]+)s;\s+([\d.]+) connections/user sec"
)
MESSAGE_LENGTH = re.compile(r"\[length ([0-9a-fA-F]+)\]")


def time_handshakes(host: str, port: int, seconds: int = 5) -> dict | None:
    result = subprocess.run(
        ["openssl", "s_time", "-connect", f"{host}:{port}", "-new",
         "-time", str(seconds)],
        capture_output=True,
        text=True,
        check=False,
    )
    match = CONNECTIONS.search(result.stdout + result.stderr)
    if not match:
        return None
    rate = float(match.group(3))
    return {
        "connections": int(match.group(1)),
        "rate_per_sec": rate,
        "mean_ms": 1000.0 / rate if rate else None,
    }


def handshake_bytes(
    host: str, port: int, groups: str, cafile: str | None = None
) -> int | None:
    cmd = ["openssl", "s_client", "-connect", f"{host}:{port}",
           "-groups", groups, "-msg"]
    if cafile:
        cmd += ["-CAfile", cafile]

    try:
        result = subprocess.run(
            cmd, input=b"", capture_output=True, timeout=30, check=False
        )
    except Exception:
        return None

    text = (result.stdout + result.stderr).decode("utf-8", "replace")
    total = 0
    for line in text.splitlines():
        if "Application Data" in line:
            break
        match = MESSAGE_LENGTH.search(line)
        if match:
            total += int(match.group(1), 16)
    return total or None


def measure(host: str, cafile: str, seconds: int) -> list[dict]:
    sides = [
        ("TLS 1.3 classical (X25519)", 8443, "X25519"),
        ("TLS 1.3 hybrid (X25519+ML-KEM-768)", 8447, "X25519MLKEM768"),
    ]
    rows = []
    for label, port, groups in sides:
        timing = time_handshakes(host, port, seconds)
        if timing is None:
            print(f"WARNING: s_time failed for {label}")
            continue
        rows.append(
            {
                "algo": label,
                "op": "handshake",
                "port": port,
                "rate_per_sec": timing["rate_per_sec"],
                "mean_ms": timing["mean_ms"],
                "bytes": handshake_bytes(host, port, groups, cafile),
            }
        )
        print(
            f"{label}: {timing['rate_per_sec']:,.0f}/s "
            f"({timing['mean_ms']:.3f} ms), "
            f"{rows[-1]['bytes']} bytes"
        )
    return rows


def to_markdown(rows: list[dict]) -> str:
    lines = [
        "### E4 -- hybrid handshake overhead",
        "",
        "| handshake | handshakes/sec | mean ms | handshake bytes |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['algo']} | {row['rate_per_sec']:,.0f} | "
            f"{row['mean_ms']:.3f} | {row['bytes']:,} |"
        )
    if len(rows) == 2:
        classical, hybrid = rows
        delta_ms = hybrid["mean_ms"] - classical["mean_ms"]
        delta_pct = 100.0 * delta_ms / classical["mean_ms"]
        delta_bytes = (hybrid["bytes"] or 0) - (classical["bytes"] or 0)
        lines += [
            "",
            f"Hybrid adds **{delta_ms:+.3f} ms** per handshake "
            f"({delta_pct:+.1f}%) and **{delta_bytes:+,} bytes**.",
            "",
        ]
    return "\n".join(lines)


def store(rows: list[dict], db: str, run_id: str) -> None:
    conn = init_db(db)
    stamp = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    for row in rows:
        conn.execute(
            "INSERT INTO bench (run_id, algo, op, ops_per_s, mean_ms, bytes,"
            " constrained, ts) VALUES (?, ?, ?, ?, ?, ?, 0, ?)",
            (
                run_id, row["algo"], row["op"], row["rate_per_sec"],
                row["mean_ms"], row["bytes"], stamp,
            ),
        )
    conn.commit()
    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="E4 hybrid handshake overhead")
    parser.add_argument("--host", default="lab")
    parser.add_argument("--cafile", default="lab/certs/ca.pem")
    parser.add_argument("--seconds", type=int, default=5)
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--run-id", default="e4-hybrid")
    parser.add_argument("--markdown-out", default="data/e4_report.md")
    args = parser.parse_args()

    rows = measure(args.host, args.cafile, args.seconds)
    if rows:
        store(rows, args.db, args.run_id)
    markdown = to_markdown(rows)
    with open(args.markdown_out, "w", encoding="utf-8") as handle:
        handle.write(markdown + "\n")
    print()
    print(markdown)


if __name__ == "__main__":
    main()
