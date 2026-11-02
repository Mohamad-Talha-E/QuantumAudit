"""TLS metadata scanner.

Records handshake metadata only: protocol version, cipher suite, negotiated
key-exchange group, certificate algorithm and key size, signature algorithm
and certificate expiry. It never sends an HTTP request and never stores
payload, which is what the ethics statement promises.

Two profiles:

* ``public`` -- normal certificate verification against system trust roots.
* ``lab``    -- trusts the lab CA (``lab/certs/ca.pem``), because the lab
  servers use a private CA. The guide's version called
  ``create_default_context()`` unconditionally, so every E1 scan failed.

Two handshakes per host:

1. Python's ``ssl`` module -- fast and gives precise certificate fields.
2. The ``openssl`` CLI -- the only way to learn the negotiated group, and
   the fallback for hosts Python's older OpenSSL cannot negotiate at all
   (for example ML-KEM-only servers).
"""

from __future__ import annotations

import datetime as dt
import socket
import ssl
import time

from cryptography import x509

from scanner import kx
from scanner.db import DEFAULT_DB, init_db, insert_finding

PUBLIC = "public"
LAB = "lab"


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def split_host_port(target: str, default_port: int = 443) -> tuple[str, int]:
    """Accept ``example.com``, ``example.com:8443`` or ``[::1]:8443``."""
    target = target.strip()
    if target.startswith("["):
        host, _, rest = target[1:].partition("]")
        port = int(rest[1:]) if rest.startswith(":") else default_port
        return host, port
    if target.count(":") == 1:
        host, _, maybe_port = target.partition(":")
        if maybe_port.isdigit():
            return host, int(maybe_port)
    return target, default_port


def _cert_algorithm(cert: x509.Certificate) -> tuple[str, int]:
    """Return a friendly algorithm name and key size for the certificate."""
    try:
        key = cert.public_key()
    except Exception:
        # A post-quantum key type this `cryptography` version does not know.
        oid = cert.tbs_certificate.subject_public_key_info.algorithm_oid
        return f"OID:{oid.dotted_string}", 0

    name = type(key).__name__
    upper = name.upper()
    if "MLDSA" in upper or "ML-DSA" in upper:
        friendly = "ML-DSA"
    elif "MLKEM" in upper or "ML-KEM" in upper:
        friendly = "ML-KEM"
    else:
        friendly = {
            "RSAPublicKey": "RSA",
            "EllipticCurvePublicKey": "EC",
            "Ed25519PublicKey": "Ed25519",
            "Ed448PublicKey": "Ed448",
            "DSAPublicKey": "DSA",
        }.get(name, name.replace("PublicKey", ""))
    return friendly, int(getattr(key, "key_size", 0) or 0)


def _cert_signature_algorithm(cert: x509.Certificate) -> str:
    oid = cert.signature_algorithm_oid
    try:
        return oid._name  # e.g. "sha256WithRSAEncryption"
    except Exception:
        return oid.dotted_string


def _apply_cert(rec: dict, cert: x509.Certificate) -> None:
    rec["cert_alg"], rec["key_size"] = _cert_algorithm(cert)
    rec["sig_alg"] = _cert_signature_algorithm(cert)
    rec["cert_expiry"] = cert.not_valid_after_utc.isoformat(timespec="seconds")


def _build_context(profile: str, cafile: str | None) -> ssl.SSLContext:
    if profile == LAB:
        if cafile:
            return ssl.create_default_context(cafile=cafile)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    return ssl.create_default_context()


def scan_host(
    target: str,
    profile: str = PUBLIC,
    cafile: str | None = None,
    timeout: int = 10,
    groups: str | None = None,
) -> dict:
    """Scan one host and return a record with every column present."""
    host, port = split_host_port(target)
    rec: dict = {
        "host": host,
        "port": port,
        "profile": profile,
        "scan_time": _now(),
        "protocol": None,
        "cipher": None,
        "kx_group": None,
        "cert_alg": None,
        "key_size": None,
        "sig_alg": None,
        "cert_expiry": None,
        "hybrid_flag": 0,
        "status": "ok",
        "error": None,
    }

    # Step 1 -- Python handshake. Its own try block, so a failure here never
    # prevents the openssl fallback below from running.
    try:
        ctx = _build_context(profile, cafile)
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as tls:
                rec["protocol"] = tls.version()
                cipher = tls.cipher()
                rec["cipher"] = cipher[0] if cipher else None

                der = tls.getpeercert(binary_form=True)
                if der:
                    _apply_cert(rec, x509.load_der_x509_certificate(der))
    except Exception as exc:  # noqa: BLE001 - every failure becomes a row
        rec["status"] = "error"
        rec["error"] = f"{type(exc).__name__}: {exc}"[:200]

    # Step 2 -- openssl CLI. Always runs: it is the only source for the
    # negotiated group, and it rescues hosts step 1 could not negotiate.
    details = kx.probe_details(
        host,
        port,
        servername=host,
        cafile=cafile if profile == LAB else None,
        groups=groups or kx.DEFAULT_GROUPS,
    )

    if rec["status"] == "error" and details["connected"]:
        rec["status"] = "ok"
        rec["error"] = None
        rec["protocol"] = details["protocol"]
        rec["cipher"] = details["cipher"]
        if details["cert_pem"]:
            try:
                _apply_cert(
                    rec, x509.load_pem_x509_certificate(details["cert_pem"].encode())
                )
            except Exception:
                pass  # keep the scan, just without certificate detail

    if details["kx_group"] != "unknown":
        rec["kx_group"] = details["kx_group"]
    else:
        rec["kx_group"] = kx.infer_from_cipher(rec["cipher"], rec["protocol"])
    rec["hybrid_flag"] = int(kx.is_hybrid(rec["kx_group"]))

    return rec


def scan_many(
    targets,
    run_id: str,
    profile: str = PUBLIC,
    db: str = DEFAULT_DB,
    delay: float = 1.0,
    cafile: str | None = None,
    resume: bool = True,
    limit: int | None = None,
    quiet: bool = False,
) -> dict:
    """Scan a list of targets, writing each result as it arrives.

    Committing per row means a crash never loses finished work, and
    ``resume=True`` skips hosts already stored under this ``run_id``.
    """
    conn = init_db(db)
    already: set[tuple[str, int]] = set()
    if resume:
        already = {
            (row["host"], row["port"])
            for row in conn.execute(
                "SELECT host, port FROM findings WHERE run_id = ?", (run_id,)
            )
        }

    targets = list(targets)
    if limit is not None:
        targets = targets[:limit]

    stats = {"ok": 0, "error": 0, "skipped": 0, "total": len(targets)}
    for index, target in enumerate(targets, start=1):
        host, port = split_host_port(target)
        if (host, port) in already:
            stats["skipped"] += 1
            continue

        rec = scan_host(target, profile=profile, cafile=cafile)
        insert_finding(conn, run_id, rec)
        stats[rec["status"]] = stats.get(rec["status"], 0) + 1

        if not quiet:
            print(
                f"[{index}/{len(targets)}] {host}:{port} -> {rec['status']}"
                f" {rec.get('kx_group') or ''} {rec.get('cert_alg') or ''}",
                flush=True,
            )

        if delay:
            time.sleep(delay)

    conn.close()
    return stats
