"""The schema document must stay in step with the real database.

If a column is added to ``scanner/db.py`` but not to ``scanner/SCHEMA.md``,
this test fails. That keeps the documentation honest instead of letting it
drift away from the code.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scanner.db import init_db

SCHEMA_DOC = Path("scanner/SCHEMA.md")
TABLES = ("findings", "scores", "bench")


def test_schema_doc_exists():
    assert SCHEMA_DOC.is_file(), "scanner/SCHEMA.md is missing"


@pytest.mark.parametrize("table", TABLES)
def test_every_column_is_documented(table, db_path):
    doc = SCHEMA_DOC.read_text(encoding="utf-8")
    assert f"`{table}`" in doc, f"table {table!r} is not in SCHEMA.md"

    conn = init_db(db_path)
    columns = [row["name"] for row in conn.execute(f"PRAGMA table_info({table})")]
    conn.close()

    assert columns, f"table {table!r} does not exist in the database"
    missing = [column for column in columns if f"`{column}`" not in doc]
    assert not missing, f"{table}: undocumented columns {missing}"


def test_upsert_key_and_error_rows_are_documented():
    doc = SCHEMA_DOC.read_text(encoding="utf-8")
    assert "ON CONFLICT (run_id, host, port)" in doc
    assert "error" in doc.lower()
