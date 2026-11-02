"""Tests for the algorithm classifier.

The important cases are the ones that were broken in the design guide:
``DSA`` inside ``ML-DSA`` and ``X25519`` inside ``X25519MLKEM768`` must not
make a post-quantum host look classical.
"""

from __future__ import annotations

import pytest

from scoring.rules import classify, components


def record(**overrides) -> dict:
    base = {
        "cert_alg": None,
        "kx_group": None,
        "sig_alg": None,
        "cipher": None,
    }
    base.update(overrides)
    return base


@pytest.mark.parametrize(
    "record_kwargs, expected",
    [
        # Pure classical: RSA certificate, classical key exchange.
        ({"cert_alg": "RSA", "kx_group": "X25519"}, "vulnerable"),
        ({"cert_alg": "EC", "kx_group": "P-256"}, "vulnerable"),
        ({"cert_alg": "Ed25519", "kx_group": "X448"}, "vulnerable"),
        # Post-quantum key exchange but classical certificate: hybrid.
        ({"cert_alg": "RSA", "kx_group": "X25519MLKEM768"}, "hybrid"),
        ({"cert_alg": "RSA", "kx_group": "MLKEM768"}, "hybrid"),
        ({"cert_alg": "RSA", "kx_group": "SecP256r1MLKEM768"}, "hybrid"),
        # Post-quantum certificate but classical key exchange: still mixed.
        ({"cert_alg": "ML-DSA", "kx_group": "X25519"}, "hybrid"),
        # Everything post-quantum: resistant.
        (
            {
                "cert_alg": "ML-DSA",
                "kx_group": "MLKEM768",
                "sig_alg": "mldsa65",
            },
            "resistant",
        ),
        # Symmetric-only weakness.
        ({"cipher": "TLS_AES_128_GCM_SHA256"}, "weakened"),
        ({"cipher": "AES128-SHA"}, "weakened"),
        # Nothing recognised.
        ({}, "unknown"),
    ],
)
def test_classify(record_kwargs, expected):
    assert classify(record(**record_kwargs)) == expected


def test_ml_dsa_is_not_read_as_dsa():
    """``ML-DSA`` contains the substring ``DSA``; it must not count as classical."""
    info = components(record(cert_alg="ML-DSA", kx_group="MLKEM768"))
    assert info["has_pq"] is True
    assert info["has_classical"] is False


def test_x25519_inside_hybrid_is_not_read_as_classical_alone():
    """A hybrid group is both PQ and classical by design -- that is why it is hybrid."""
    info = components(record(cert_alg="RSA", kx_group="X25519MLKEM768"))
    assert info["has_pq"] is True
    assert info["has_classical"] is True


def test_underscores_are_normalised():
    """Real cipher names use underscores: TLS_AES_128_GCM_SHA256."""
    assert classify(record(cipher="TLS_AES_128_GCM_SHA256")) == "weakened"


def test_asymmetric_evidence_wins_over_symmetric():
    """AES-128 next to RSA is still a vulnerable host, not merely weakened."""
    assert (
        classify(record(cert_alg="RSA", kx_group="X25519", cipher="TLS_AES_128_GCM_SHA256"))
        == "vulnerable"
    )


def test_components_reports_evidence():
    info = components(record(cert_alg="RSA", kx_group="X25519MLKEM768"))
    assert info["certificate"] == "RSA"
    assert info["key_exchange"] == "X25519MLKEM768"
    assert info["symmetric"] == "UNKNOWN"
