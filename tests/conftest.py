"""Shared fixtures for the QuantumAudit test suite."""

from __future__ import annotations

import pytest

from scanner.db import init_db


@pytest.fixture()
def db_path(tmp_path):
    """A throwaway SQLite database with the real schema."""
    path = str(tmp_path / "test.db")
    conn = init_db(path)
    conn.close()
    return path
