"""Tests for OpenSSL output parsing.

These strings are copied from real OpenSSL 3.5 output captured during the
build, so the tests catch the exact quirks that broke earlier versions.
"""

from __future__ import annotations

import pytest

from scanner.kx import _group_from_text, infer_from_cipher, is_hybrid

TLS13 = """
CONNECTION ESTABLISHED
Protocol version: TLSv1.3
Ciphersuite: TLS_AES_256_GCM_SHA384
Negotiated TLS1.3 group: X25519MLKEM768
"""

TLS12_ECDH = "Peer Temp Key: ECDH, prime256v1, 256 bits\n"

TLS12_X25519 = "Peer Temp Key: X25519, 253 bits\n"

OLD_SERVER_TEMP_KEY = "Server Temp Key: ECDH, P-384, 384 bits\n"

FAILED = "Peer Temp Key: <NULL>\n"

TLS13_FAILED = "Negotiated TLS1.3 group: <NULL>\n"


@pytest.mark.parametrize(
    "text, expected",
    [
        (TLS13, "X25519MLKEM768"),
        (TLS12_ECDH, "P-256"),          # curve alias applied
        (TLS12_X25519, "X25519"),       # method label dropped
        (OLD_SERVER_TEMP_KEY, "P-384"),
        (FAILED, "unknown"),            # <NULL> is not a group name
        (TLS13_FAILED, "unknown"),      # same leak in the TLS 1.3 line
        ("nothing useful here", "unknown"),
    ],
)
def test_group_parsing(text, expected):
    assert _group_from_text(text) == expected


def test_hybrid_detection():
    assert is_hybrid("X25519MLKEM768") is True
    assert is_hybrid("MLKEM768") is True
    assert is_hybrid("SecP256r1MLKEM768") is True
    assert is_hybrid("X25519") is False
    assert is_hybrid(None) is False


@pytest.mark.parametrize(
    "cipher, protocol, expected",
    [
        ("ECDHE-RSA-AES256-GCM-SHA384", "TLSv1.2", "ECDHE"),
        ("DHE-RSA-AES256-GCM-SHA384", "TLSv1.2", "DHE"),
        ("AES128-SHA", "TLSv1.2", "RSA"),
        (None, "TLSv1.2", "unknown"),
        ("TLS_AES_256_GCM_SHA384", "TLSv1.3", "unknown"),
    ],
)
def test_infer_from_cipher(cipher, protocol, expected):
    assert infer_from_cipher(cipher, protocol) == expected
