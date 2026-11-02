"""Tests for the Mosca risk model and the naive baseline."""

from __future__ import annotations

import pytest

from scoring.mosca import naive_score, safe_window, scenario_name, score

VULNERABLE = {"cert_alg": "RSA", "kx_group": "X25519", "cipher": "TLS_AES_256_GCM_SHA384"}
HYBRID = {"cert_alg": "RSA", "kx_group": "X25519MLKEM768"}
RESISTANT = {"cert_alg": "ML-DSA", "kx_group": "MLKEM768", "sig_alg": "mldsa65"}
UNKNOWN = {}


def test_safe_window_is_horizon_minus_migration():
    assert safe_window(3, 15) == 12
    assert safe_window(5, 20) == 15


def test_scenario_name_is_stable():
    assert scenario_name(15, 3, 15) == "x15_y3_z15"


def test_long_shelf_life_is_high_risk():
    level, reason, step = score(VULNERABLE, shelf_life_years=15, quantum_years=15)
    assert level == "high"
    assert "safe window 12y" in reason
    assert "ML-KEM" in step


def test_short_shelf_life_is_low_risk():
    level, _, _ = score(VULNERABLE, shelf_life_years=5, quantum_years=15)
    assert level == "low"


def test_middle_shelf_life_is_medium_risk():
    level, _, _ = score(VULNERABLE, shelf_life_years=10, quantum_years=15)
    assert level == "medium"


def test_distant_horizon_lowers_risk():
    """A quantum computer 20 years away leaves time to migrate."""
    level, _, _ = score(VULNERABLE, shelf_life_years=15, quantum_years=20)
    assert level == "medium"


def test_hybrid_and_resistant_are_low():
    assert score(HYBRID)[0] == "low"
    assert score(RESISTANT)[0] == "low"


def test_unknown_is_medium_for_manual_review():
    assert score(UNKNOWN)[0] == "medium"


def test_naive_flags_every_classical_and_hybrid_host():
    assert naive_score(VULNERABLE)[0] == "high"
    assert naive_score(HYBRID)[0] == "high"
    assert naive_score(RESISTANT)[0] == "low"


def test_naive_is_never_lower_than_contextual():
    """The whole point of E6: context can only reduce a naive high verdict."""
    for shelf in (5, 10, 15, 25):
        for horizon in (10, 15, 20):
            contextual = score(VULNERABLE, shelf_life_years=shelf, quantum_years=horizon)[0]
            assert contextual in ("low", "medium", "high")
            assert naive_score(VULNERABLE)[0] == "high"
