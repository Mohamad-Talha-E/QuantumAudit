"""Tests for target parsing and Tranco sampling."""

from __future__ import annotations

import pytest

from scanner.scan import split_host_port
from scanner.tranco import sample


@pytest.mark.parametrize(
    "target, expected",
    [
        ("example.com", ("example.com", 443)),
        ("example.com:8443", ("example.com", 8443)),
        ("lab:8443", ("lab", 8443)),
        ("[::1]:8443", ("::1", 8443)),
        ("[2001:db8::1]", ("2001:db8::1", 443)),
        ("  example.com  ", ("example.com", 443)),
        # A bare IPv6 address keeps the default port.
        ("::1", ("::1", 443)),
    ],
)
def test_split_host_port(target, expected):
    assert split_host_port(target) == expected


def test_tranco_sample_is_deterministic():
    domains = [f"site{i}.example" for i in range(500)]
    first = sample(domains, n=25, seed=413, pool=200)
    second = sample(domains, n=25, seed=413, pool=200)
    assert first == second
    assert len(first) == 25


def test_tranco_sample_changes_with_seed():
    domains = [f"site{i}.example" for i in range(500)]
    assert sample(domains, n=25, seed=1, pool=200) != sample(
        domains, n=25, seed=2, pool=200
    )


def test_tranco_sample_respects_pool():
    domains = [f"site{i}.example" for i in range(500)]
    picked = sample(domains, n=50, seed=413, pool=100)
    assert set(picked) <= set(domains[:100])


def test_tranco_sample_handles_short_lists():
    domains = ["a.example", "b.example"]
    assert sorted(sample(domains, n=10, seed=413, pool=100)) == domains
