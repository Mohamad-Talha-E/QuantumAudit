"""Algorithm classification.

Two kinds of evidence are deliberately kept apart:

* **asymmetric** -- certificate key type, key-exchange group, signature
  algorithm. This is what a quantum computer actually breaks.
* **symmetric** -- the bulk cipher. Weakened by Grover's algorithm, but NIST
  still permits AES-128, so it only matters once the asymmetric side is safe.

Why this file was rewritten:

* The guide searched one blob of text with patterns like ``AES-128``. Real
  OpenSSL cipher names use underscores (``TLS_AES_128_GCM_SHA256``), so those
  patterns never matched and the ``weakened`` class was dead code.
* ``DSA`` appears inside ``ML-DSA`` and ``X25519`` inside ``X25519MLKEM768``.
  Matching naively would label post-quantum algorithms as classical. We strip
  the post-quantum tokens first, then look for classical ones.
"""

from __future__ import annotations

import re

RESISTANT = re.compile(r"(ML-?KEM|ML-?DSA|SLH-?DSA|FALCON|SPHINCS)")
VULNERABLE = re.compile(r"(RSA|ECDH|ECDSA|DHE|DSA|ED25519|ED448|X25519|X448|SECP|P-256|P-384)")
# OpenSSL writes both "AES-128" (TLS 1.3 names) and "AES128" (TLS 1.2 names),
# so the separator is optional. DES-CBC3 is the real name for 3DES suites.
WEAKENED = re.compile(r"(AES-?128|3DES|DES-CBC3|DES-CBC|RC4|SHA1|MD5)")

ASYM_FIELDS = ("cert_alg", "kx_group", "sig_alg")
SYM_FIELDS = ("cipher",)

#: Classes in the order they should be reported.
CLASSES = ("hybrid", "resistant", "vulnerable", "weakened", "unknown")


def normalise(value) -> str:
    """Upper-case and turn underscores into hyphens, so patterns match."""
    if value is None:
        return ""
    return str(value).upper().replace("_", "-")


def _asymmetric_text(record: dict) -> str:
    return " ".join(normalise(record.get(field)) for field in ASYM_FIELDS)


def _symmetric_text(record: dict) -> str:
    return " ".join(normalise(record.get(field)) for field in SYM_FIELDS)


def _classical_only(text: str) -> str:
    """Remove post-quantum tokens so ``ML-DSA`` is not read as ``DSA``."""
    return RESISTANT.sub(" ", text)


def components(record: dict) -> dict:
    """Return the evidence per component, for explanations."""
    asym = _asymmetric_text(record)
    sym = _symmetric_text(record)
    return {
        "certificate": normalise(record.get("cert_alg")) or "UNKNOWN",
        "key_exchange": normalise(record.get("kx_group")) or "UNKNOWN",
        "signature": normalise(record.get("sig_alg")) or "UNKNOWN",
        "symmetric": normalise(record.get("cipher")) or "UNKNOWN",
        "has_pq": bool(RESISTANT.search(asym)),
        "has_classical": bool(VULNERABLE.search(_classical_only(asym))),
        "symmetric_weak": bool(WEAKENED.search(sym)),
    }


def classify(record: dict) -> str:
    """Return one of: hybrid, resistant, vulnerable, weakened, unknown."""
    info = components(record)

    if info["has_pq"] and info["has_classical"]:
        return "hybrid"
    if info["has_pq"]:
        return "resistant"
    if info["has_classical"]:
        return "vulnerable"
    if info["symmetric_weak"]:
        return "weakened"
    return "unknown"
