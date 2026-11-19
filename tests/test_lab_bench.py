"""Tests for the benchmark summary helper.

``summarise`` is pure: it takes a list of numbers and returns statistics, so it
can be tested without running OpenSSL or starting the lab.
"""

from __future__ import annotations

import pytest

from lab.bench import summarise


def test_summarise_three_samples():
    result = summarise([10.0, 20.0, 30.0])
    assert result["count"] == 3
    assert result["mean"] == 20.0
    assert result["stdev"] == pytest.approx(10.0)
    assert result["min"] == 10.0
    assert result["max"] == 30.0


def test_summarise_single_sample_has_zero_spread():
    result = summarise([5.0])
    assert result["count"] == 1
    assert result["mean"] == 5.0
    assert result["stdev"] == 0.0


def test_summarise_empty_is_none_not_an_error():
    result = summarise([])
    assert result["count"] == 0
    assert result["mean"] is None
    assert result["stdev"] is None
    assert result["min"] is None
    assert result["max"] is None
