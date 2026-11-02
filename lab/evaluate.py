"""E1 -- scanner accuracy against the controlled lab.

The lab has 20 servers whose configuration we chose ourselves, so we know the
correct answer. This script scans all of them and compares what the scanner
reported with the answer key in ``lab/lab_manifest.json``.

Reported metrics:

* per-field accuracy -- did the scanner get protocol / cert / key size /
  group / hybrid flag right, field by field;
* exact-match rate -- did it get the whole row right;
* precision, recall and F1 for the "is this host post-quantum protected"
  decision, which is the binary call the risk score depends on.

The module brief asks for at least 0.80 precision and recall.
"""

from __future__ import annotations

import argparse
import json

from scanner.db import DEFAULT_DB, init_db, insert_finding
from scanner.scan import LAB, scan_host

FIELDS = ("protocol", "cert_alg", "key_size", "kx_group", "hybrid_flag")


def load_manifest(path: str = "lab/lab_manifest.json") -> list[dict]:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)["servers"]


def _expected(entry: dict) -> dict:
    return {
        "protocol": entry["protocol"],
        "cert_alg": entry["cert_alg"],
        "key_size": entry["key_size"],
        "kx_group": entry["kx_group"],
        "hybrid_flag": int(entry["hybrid"]),
    }


def _safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def evaluate(
    host: str = "lab",
    cafile: str = "lab/certs/ca.pem",
    manifest_path: str = "lab/lab_manifest.json",
    db: str | None = None,
    run_id: str | None = None,
) -> dict:
    entries = load_manifest(manifest_path)
    rows: list[dict] = []
    conn = init_db(db or DEFAULT_DB) if run_id else None

    for entry in entries:
        target = f"{host}:{entry['port']}"
        record = scan_host(target, profile=LAB, cafile=cafile)
        if conn:
            insert_finding(conn, run_id, record)

        expected = _expected(entry)
        actual = {field: record.get(field) for field in FIELDS}
        mismatches = [
            f"{field}: expected {expected[field]!r}, got {actual[field]!r}"
            for field in FIELDS
            if expected[field] != actual[field]
        ]
        rows.append(
            {
                "port": entry["port"],
                "name": entry["name"],
                "status": record["status"],
                "expected": expected,
                "actual": actual,
                "mismatches": mismatches,
                "exact": not mismatches and record["status"] == "ok",
            }
        )

    if conn:
        conn.close()

    total = len(rows)
    field_accuracy = {
        field: _safe_div(
            sum(1 for row in rows if row["expected"][field] == row["actual"][field]),
            total,
        )
        for field in FIELDS
    }
    exact = _safe_div(sum(1 for row in rows if row["exact"]), total)

    # Binary decision: is the host post-quantum protected?
    tp = sum(
        1
        for row in rows
        if row["expected"]["hybrid_flag"] == 1 and row["actual"]["hybrid_flag"] == 1
    )
    fp = sum(
        1
        for row in rows
        if row["expected"]["hybrid_flag"] == 0 and row["actual"]["hybrid_flag"] == 1
    )
    fn = sum(
        1
        for row in rows
        if row["expected"]["hybrid_flag"] == 1 and row["actual"]["hybrid_flag"] == 0
    )
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = _safe_div(2 * precision * recall, precision + recall)

    return {
        "host": host,
        "servers": total,
        "field_accuracy": field_accuracy,
        "exact_match": exact,
        "pq_precision": precision,
        "pq_recall": recall,
        "pq_f1": f1,
        "rows": rows,
        "mismatch_count": sum(1 for row in rows if row["mismatches"]),
    }


def to_markdown(report: dict) -> str:
    lines = [
        "### E1 -- scanner accuracy",
        "",
        f"Servers scanned: **{report['servers']}**  ",
        f"Rows exactly correct: **{report['exact_match'] * 100:.1f}%**  ",
        f"Rows with at least one mismatch: **{report['mismatch_count']}**",
        "",
        "| field | accuracy |",
        "|---|---|",
    ]
    for field, value in report["field_accuracy"].items():
        lines.append(f"| {field} | {value * 100:.1f}% |")
    lines += [
        "",
        f"Post-quantum detection: precision **{report['pq_precision']:.2f}**, "
        f"recall **{report['pq_recall']:.2f}**, F1 **{report['pq_f1']:.2f}**",
        "",
    ]

    problems = [row for row in report["rows"] if row["mismatches"]]
    if problems:
        lines.append("**Mismatches**")
        lines.append("")
        lines.append("| port | server | mismatch |")
        lines.append("|---|---|---|")
        for row in problems:
            detail = "; ".join(row["mismatches"]).replace("|", "\\|")
            lines.append(f"| {row['port']} | {row['name']} | {detail} |")
        lines.append("")
    else:
        lines.append("No mismatches: every lab configuration was identified correctly.")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="E1 scanner accuracy")
    parser.add_argument("--host", default="lab", help="lab hostname or IP")
    parser.add_argument("--cafile", default="lab/certs/ca.pem")
    parser.add_argument("--manifest", default="lab/lab_manifest.json")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--run-id", default="e1-lab")
    parser.add_argument("--json-out", default="data/e1_report.json")
    parser.add_argument("--markdown-out", default="data/e1_report.md")
    args = parser.parse_args()

    report = evaluate(
        host=args.host,
        cafile=args.cafile,
        manifest_path=args.manifest,
        db=args.db,
        run_id=args.run_id,
    )

    with open(args.json_out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    markdown = to_markdown(report)
    with open(args.markdown_out, "w", encoding="utf-8") as handle:
        handle.write(markdown + "\n")

    print(markdown)


if __name__ == "__main__":
    main()
