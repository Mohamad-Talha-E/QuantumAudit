"""Key-exchange detection and OpenSSL fallback.

Python's built-in ``ssl`` module cannot report the negotiated key-exchange
group, and the OpenSSL bundled with CPython (3.0.x) is too old to negotiate
ML-KEM-only groups or ML-DSA certificates. So we also ask the ``openssl``
command line, which inside our container is 3.5.x.

The ``openssl`` probe serves two purposes:

1. it tells us the negotiated group;
2. when Python's handshake fails (for example a server that only offers
   ML-KEM-768), it supplies the protocol, cipher and certificate instead.

If ``openssl`` is missing everything degrades to ``"unknown"`` rather than
raising, so a scan never loses the rest of its fields.
"""

from __future__ import annotations

import re
import shutil
import subprocess

# Hybrid groups are offered first so a capable server picks them. The
# SecP*MLKEM* variants are included because some servers only accept those.
DEFAULT_GROUPS = (
    "X25519MLKEM768:SecP256r1MLKEM768:SecP384r1MLKEM1024:"
    "MLKEM768:X25519:secp256r1:secp384r1:x448"
)

_TLS13_GROUP = re.compile(r"Negotiated TLS1\.3 group:\s*([^\s,]+)")
_TEMP_KEY_LINE = re.compile(r"(?:Server|Peer) Temp Key:\s*([^\r\n]+)")
_PROTOCOL = re.compile(r"Protocol\s*:\s*(\S+)")
_CIPHER = re.compile(r"Cipher is (\S+)")
_CERT = re.compile(
    r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", re.DOTALL
)

_HYBRID_HINTS = ("MLKEM", "ML-KEM", "KYBER")
_EPHEMERAL_LABELS = {"ECDH", "ECDHE", "DH", "DHE"}

# OpenSSL prints the historical curve name for TLS 1.2; the manifest and the
# report use the standard short name.
_CURVE_ALIASES = {
    "PRIME256V1": "P-256",
    "SECP384R1": "P-384",
    "SECP521R1": "P-521",
    "SECP256K1": "secp256k1",
}


def openssl_available() -> bool:
    return shutil.which("openssl") is not None


def _group_from_text(text: str) -> str:
    """Extract the group name from s_client output.

    TLS 1.3: ``Negotiated TLS1.3 group: X25519MLKEM768``
    TLS 1.2: ``Peer Temp Key: ECDH, P-256, 256 bits``
             (the first token is the method, the second the curve)
    """
    match = _TLS13_GROUP.search(text)
    if match:
        group = match.group(1)
        return "unknown" if group.startswith("<") else group

    match = _TEMP_KEY_LINE.search(text)
    if not match:
        return "unknown"

    parts = [part.strip() for part in match.group(1).split(",") if part.strip()]
    if not parts:
        return "unknown"
    if parts[0].upper() in _EPHEMERAL_LABELS and len(parts) > 1:
        group = parts[1]
    else:
        group = parts[0]

    # Failed handshakes sometimes print "<NULL>" instead of a group name.
    if group.startswith("<"):
        return "unknown"
    return _CURVE_ALIASES.get(group.upper(), group)


def probe_details(
    host: str,
    port: int = 443,
    servername: str | None = None,
    cafile: str | None = None,
    groups: str = DEFAULT_GROUPS,
    timeout: int = 20,
) -> dict:
    """Run one ``openssl s_client`` handshake and parse what it reports."""
    empty = {
        "connected": False,
        "kx_group": "unknown",
        "protocol": None,
        "cipher": None,
        "cert_pem": None,
    }
    if not openssl_available():
        return empty

    cmd = [
        "openssl", "s_client",
        "-connect", f"{host}:{port}",
        "-groups", groups,
        "-showcerts",
    ]
    if servername:
        cmd += ["-servername", servername]
    if cafile:
        cmd += ["-CAfile", cafile]
    else:
        cmd += ["-verify_quiet"]

    try:
        proc = subprocess.run(
            cmd, input=b"", capture_output=True, timeout=timeout, check=False
        )
    except Exception:
        return empty

    text = (proc.stdout + proc.stderr).decode("utf-8", "replace")
    cert = _CERT.search(text)
    protocol = _PROTOCOL.search(text)
    cipher = _CIPHER.search(text)

    cipher_name = cipher.group(1) if cipher else None
    # A server can accept TCP, then close before the handshake finishes. In
    # that case OpenSSL prints "Cipher is (NONE)"; it is not a successful
    # handshake and must not be recorded as one.
    connected = bool(cipher_name) and cipher_name != "(NONE)"

    return {
        "connected": connected,
        "kx_group": _group_from_text(text) if connected else "unknown",
        "protocol": protocol.group(1) if (protocol and connected) else None,
        "cipher": cipher_name if connected else None,
        "cert_pem": cert.group(0) if cert else None,
    }


def probe(
    host: str,
    port: int = 443,
    servername: str | None = None,
    cafile: str | None = None,
    groups: str = DEFAULT_GROUPS,
    timeout: int = 20,
) -> str:
    """Return just the negotiated group name."""
    return probe_details(
        host, port, servername=servername, cafile=cafile, groups=groups, timeout=timeout
    )["kx_group"]


def is_hybrid(group: str | None) -> bool:
    if not group:
        return False
    upper = group.upper()
    return any(hint in upper for hint in _HYBRID_HINTS)


def infer_from_cipher(cipher: str | None, protocol: str | None = None) -> str:
    """Fallback when no group line is printed at all.

    The cipher suite still reveals whether an ephemeral key exchange was used,
    which is enough to decide whether the host is quantum-vulnerable.
    """
    if not cipher:
        return "unknown"
    name = cipher.upper()
    if "ECDHE" in name:
        return "ECDHE"
    if "DHE" in name:
        return "DHE"
    if protocol and protocol.upper() in ("TLSV1", "TLSV1.1", "TLSV1.2"):
        # A TLS 1.2 suite with no ECDHE/DHE is static RSA/DH key transport.
        return "RSA"
    return "unknown"
