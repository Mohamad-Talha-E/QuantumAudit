"""Command line interface for QuantumAudit.

Every experiment is reproducible with one command, for example::

    python -m scanner.cli scan-lab          # E1
    python -m scanner.cli scan-tranco       # E2
    python -m scanner.cli score --run-id e2-tranco
    python -m scanner.cli sensitivity --run-id e2-tranco   # E6
    python -m scanner.cli summary --run-id e2-tranco

All of these are meant to run inside the toolbox container::

    docker compose run --rm tools python -m scanner.cli --help
"""

from __future__ import annotations

import argparse
import json
import sys

from scanner.db import DEFAULT_DB, init_db
from scanner.scan import LAB, PUBLIC, scan_many
from scanner.tranco import download, load_domains, sample
from scoring.score_db import score_all_scenarios, score_run
from scoring.sensitivity import build_table, to_markdown


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--db", default=DEFAULT_DB, help="SQLite database path")


def cmd_scan_lab(args: argparse.Namespace) -> int:
    """Scan the controlled lab (E1)."""
    ports = list(range(args.first_port, args.last_port + 1))
    targets = [f"{args.host}:{port}" for port in ports]
    stats = scan_many(
        targets,
        run_id=args.run_id,
        profile=LAB,
        db=args.db,
        cafile=args.cafile,
        delay=args.delay,
        resume=not args.fresh,
    )
    print(json.dumps(stats, indent=2))
    return 0 if stats.get("error", 0) == 0 else 1


def cmd_scan_tranco(args: argparse.Namespace) -> int:
    """Scan a reproducible Tranco sample (E2)."""
    csv_path = download(args.csv)
    domains = load_domains(csv_path)
    if not domains:
        print(f"No domains found in {csv_path}", file=sys.stderr)
        return 2

    picked = sample(domains, n=args.n, seed=args.seed, pool=args.pool)
    print(
        f"Tranco: {len(domains)} domains available, "
        f"sampling {len(picked)} from the top {args.pool} (seed {args.seed})"
    )
    stats = scan_many(
        picked,
        run_id=args.run_id,
        profile=PUBLIC,
        db=args.db,
        delay=args.delay,
        resume=not args.fresh,
    )
    print(json.dumps(stats, indent=2))
    return 0


def cmd_scan_list(args: argparse.Namespace) -> int:
    """Scan an explicit list of targets, one per line."""
    with open(args.file, encoding="utf-8") as handle:
        targets = [
            line.strip()
            for line in handle
            if line.strip() and not line.startswith("#")
        ]
    stats = scan_many(
        targets,
        run_id=args.run_id,
        profile=args.profile,
        db=args.db,
        cafile=args.cafile,
        delay=args.delay,
        resume=not args.fresh,
    )
    print(json.dumps(stats, indent=2))
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    """Score one run under a single planning scenario."""
    if args.all_scenarios:
        written = score_all_scenarios(
            args.run_id,
            db=args.db,
            horizons=tuple(args.horizons),
            shelf_lives=tuple(args.shelf_lives),
            migration_years=args.migration,
        )
    else:
        written = score_run(
            args.run_id,
            db=args.db,
            shelf_life_years=args.shelf,
            migration_years=args.migration,
            quantum_years=args.horizon,
        )
    print(f"Scored {written} finding(s) for run '{args.run_id}'")
    return 0


def cmd_sensitivity(args: argparse.Namespace) -> int:
    """Build the E6 sensitivity table."""
    table = build_table(
        args.run_id,
        db=args.db,
        horizons=tuple(args.horizons),
        shelf_lives=tuple(args.shelf_lives),
        migration_years=args.migration,
    )
    markdown = to_markdown(table)
    with open(args.markdown_out, "w", encoding="utf-8") as handle:
        handle.write(markdown + "\n")
    with open(args.json_out, "w", encoding="utf-8") as handle:
        json.dump(
            {
                **table,
                "per_scenario": {
                    key: dict(counts) for key, counts in table["per_scenario"].items()
                },
                "classes": dict(table["classes"]),
            },
            handle,
            indent=2,
        )
    print(markdown)
    return 0


def _error_category(message: str | None) -> str:
    """Bucket a failure message so the report can say *why* hosts failed."""
    text = (message or "").lower()
    if "gaierror" in text or "name or service" in text or "name resolution" in text:
        return "dns"
    if "timed out" in text or "timeout" in text:
        return "timeout"
    if "ssl" in text or "handshake" in text or "certificate" in text:
        return "tls"
    if "refused" in text or "unreachable" in text:
        return "network"
    return "other"


def cmd_summary(args: argparse.Namespace) -> int:
    """Print a short overview of one run."""
    conn = init_db(args.db)
    rows = conn.execute(
        """
        SELECT
            COUNT(*)                                        AS hosts,
            SUM(status = 'ok')                              AS ok,
            SUM(status = 'error')                           AS failed,
            SUM(hybrid_flag = 1)                            AS hybrid,
            SUM(kx_group LIKE '%MLKEM%'
                OR kx_group LIKE '%ML-KEM%')                AS pq_key_exchange
        FROM findings
        WHERE run_id = ?
        """,
        (args.run_id,),
    ).fetchone()

    protocols = conn.execute(
        """
        SELECT protocol, COUNT(*) AS count
        FROM findings WHERE run_id = ? AND status = 'ok'
        GROUP BY protocol ORDER BY count DESC
        """,
        (args.run_id,),
    ).fetchall()

    certs = conn.execute(
        """
        SELECT cert_alg, COUNT(*) AS count
        FROM findings WHERE run_id = ? AND status = 'ok'
        GROUP BY cert_alg ORDER BY count DESC
        """,
        (args.run_id,),
    ).fetchall()

    scored = conn.execute(
        """
        SELECT scenario, score_contextual, COUNT(*) AS count
        FROM scores WHERE finding_id IN (
            SELECT id FROM findings WHERE run_id = ?
        )
        GROUP BY scenario, score_contextual
        ORDER BY scenario, score_contextual
        """,
        (args.run_id,),
    ).fetchall()
    errors = conn.execute(
        """
        SELECT host, error FROM findings
        WHERE run_id = ? AND status = 'error'
        ORDER BY host
        """,
        (args.run_id,),
    ).fetchall()
    conn.close()

    print(f"Run: {args.run_id}")
    print(json.dumps(dict(rows) if rows else {}, indent=2))
    print("\nProtocols:")
    for row in protocols:
        print(f"  {row['protocol'] or 'unknown':10} {row['count']}")
    print("\nCertificate algorithms:")
    for row in certs:
        print(f"  {row['cert_alg'] or 'unknown':10} {row['count']}")
    if scored:
        print("\nRisk verdicts:")
        current = None
        for row in scored:
            if row["scenario"] != current:
                current = row["scenario"]
                print(f"  [{current}]")
            print(f"    {row['score_contextual']:8} {row['count']}")
    if args.errors and errors:
        print("\nFailed hosts:")
        for row in errors:
            print(f"  {row['host']:32} {row['error']}")
    if errors:
        counts: dict[str, int] = {}
        for row in errors:
            category = _error_category(row["error"])
            counts[category] = counts.get(category, 0) + 1
        print("\nFailure categories:")
        for category, count in sorted(counts.items(), key=lambda item: -item[1]):
            print(f"  {category:10} {count}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quantumaudit",
        description="TLS cryptographic inventory and post-quantum risk scanner.",
    )
    _add_common(parser)
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- scan-lab -------------------------------------------------------
    lab = subparsers.add_parser("scan-lab", help="scan the controlled lab (E1)")
    _add_common(lab)
    lab.add_argument("--host", default="lab")
    lab.add_argument("--cafile", default="lab/certs/ca.pem")
    lab.add_argument("--first-port", type=int, default=8443)
    lab.add_argument("--last-port", type=int, default=8462)
    lab.add_argument("--run-id", default="e1-lab")
    lab.add_argument("--delay", type=float, default=0.0)
    lab.add_argument("--fresh", action="store_true", help="rescan even if stored")
    lab.set_defaults(func=cmd_scan_lab)

    # --- scan-tranco ----------------------------------------------------
    tranco = subparsers.add_parser("scan-tranco", help="scan a Tranco sample (E2)")
    _add_common(tranco)
    tranco.add_argument("--csv", default="data/tranco/top-1m.csv")
    tranco.add_argument("--n", type=int, default=100)
    tranco.add_argument("--seed", type=int, default=413)
    tranco.add_argument("--pool", type=int, default=10000)
    tranco.add_argument("--run-id", default="e2-tranco")
    tranco.add_argument("--delay", type=float, default=0.5)
    tranco.add_argument("--fresh", action="store_true")
    tranco.set_defaults(func=cmd_scan_tranco)

    # --- scan-list ------------------------------------------------------
    scan_list = subparsers.add_parser("scan-list", help="scan targets from a file")
    _add_common(scan_list)
    scan_list.add_argument("file")
    scan_list.add_argument("--profile", choices=[PUBLIC, LAB], default=PUBLIC)
    scan_list.add_argument("--cafile", default=None)
    scan_list.add_argument("--run-id", default="custom")
    scan_list.add_argument("--delay", type=float, default=0.5)
    scan_list.add_argument("--fresh", action="store_true")
    scan_list.set_defaults(func=cmd_scan_list)

    # --- score ----------------------------------------------------------
    score = subparsers.add_parser("score", help="score a run")
    _add_common(score)
    score.add_argument("--run-id", required=True)
    score.add_argument("--shelf", type=int, default=15)
    score.add_argument("--migration", type=int, default=3)
    score.add_argument("--horizon", type=int, default=15)
    score.add_argument(
        "--all-scenarios",
        action="store_true",
        help="score every horizon/shelf-life combination (E6 input)",
    )
    score.add_argument("--horizons", type=int, nargs="+", default=[10, 15, 20])
    score.add_argument("--shelf-lives", type=int, nargs="+", default=[5, 10, 15, 25])
    score.set_defaults(func=cmd_score)

    # --- sensitivity ----------------------------------------------------
    sensitivity = subparsers.add_parser(
        "sensitivity", help="E6 sensitivity table"
    )
    _add_common(sensitivity)
    sensitivity.add_argument("--run-id", required=True)
    sensitivity.add_argument("--migration", type=int, default=3)
    sensitivity.add_argument("--horizons", type=int, nargs="+", default=[10, 15, 20])
    sensitivity.add_argument("--shelf-lives", type=int, nargs="+", default=[5, 10, 15, 25])
    sensitivity.add_argument("--markdown-out", default="data/e6_report.md")
    sensitivity.add_argument("--json-out", default="data/e6_report.json")
    sensitivity.set_defaults(func=cmd_sensitivity)

    # --- summary --------------------------------------------------------
    summary = subparsers.add_parser("summary", help="show a run overview")
    _add_common(summary)
    summary.add_argument("--run-id", required=True)
    summary.add_argument(
        "--errors", action="store_true", help="list hosts that failed to scan"
    )
    summary.set_defaults(func=cmd_summary)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
