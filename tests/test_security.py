"""Security regression tests for the account lookup.

The key test here (:func:`test_get_account_resists_sql_injection`) is expected
to **fail** on the deliberately vulnerable demo branch and **pass** on the
secure baseline (and again once the AI fixer restores a parameterized query).

These tests are safe and local: they use fictional data and a throwaway
in-memory database. They validate that the implementation *resists* a malformed
input; they are not, and must not become, a general-purpose exploitation tool.
"""

from __future__ import annotations

import sqlite3
from typing import Iterator

import pytest

from app.accounts import get_account
from app.database import get_connection


@pytest.fixture()
def db() -> Iterator[sqlite3.Connection]:
    connection = get_connection(":memory:")
    yield connection
    connection.close()


def test_get_account_resists_sql_injection(db: sqlite3.Connection) -> None:
    """A classic tautology payload must not leak rows.

    With a parameterized query, the string ``"0 OR 1=1"`` is treated purely as
    a value: it matches no integer ``id``, so the function returns ``None``.

    With unsafe string interpolation the same input becomes
    ``... WHERE id = 0 OR 1=1``, which matches every row and returns one — so
    this assertion fails, flagging the injection.
    """
    malicious_input = "0 OR 1=1"
    result = get_account(db, malicious_input)
    assert result is None, (
        "SQL injection detected: a tautology payload returned a row. "
        "The query is not safely parameterizing user input."
    )


def test_injection_cannot_dump_other_accounts(db: sqlite3.Connection) -> None:
    """A UNION-style payload must not exfiltrate unrelated data."""
    payload = "1 UNION SELECT id, name, email FROM accounts"
    result = get_account(db, payload)
    # Safe behaviour: the payload is a value that matches no id -> None.
    assert result is None, (
        "SQL injection detected: a UNION payload altered the query results."
    )


def test_injection_cannot_drop_table(db: sqlite3.Connection) -> None:
    """Even a destructive payload must leave the data intact and not error.

    With parameterization the input ``"1; DROP TABLE accounts"`` is bound as a
    single value, so nothing is dropped and no error is raised. With unsafe
    interpolation the same input becomes two statements, which SQLite rejects —
    so this test fails there, flagging the injection.
    """
    try:
        get_account(db, "1; DROP TABLE accounts")
    except sqlite3.Error as exc:  # pragma: no cover - only hit on vulnerable code
        pytest.fail(f"Lookup raised on malicious input (injection point): {exc!r}")

    remaining = db.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
    assert remaining == 3, "Data was modified by a malicious lookup input."
