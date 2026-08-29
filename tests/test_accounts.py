"""Functional tests for the account lookup.

These prove that normal behaviour works and keeps working after remediation:
valid IDs return the right account, and unusual input does not crash the app.
"""

from __future__ import annotations

import sqlite3
from typing import Iterator

import pytest

from app.accounts import get_account
from app.database import get_connection


@pytest.fixture()
def db() -> Iterator[sqlite3.Connection]:
    """A fresh, seeded in-memory database for each test."""
    connection = get_connection(":memory:")
    yield connection
    connection.close()


def test_valid_account_id_returns_expected_account(db: sqlite3.Connection) -> None:
    assert get_account(db, 1) == (1, "Alice Example", "alice@example.test")
    assert get_account(db, 2) == (2, "Bob Example", "bob@example.test")
    assert get_account(db, 3) == (3, "Carol Example", "carol@example.test")


def test_unknown_account_id_returns_none(db: sqlite3.Connection) -> None:
    # A well-formed but non-existent id should simply return nothing.
    assert get_account(db, 999) is None


def test_malformed_input_does_not_crash(db: sqlite3.Connection) -> None:
    # Odd input must fail safely (return None), never raise.
    for weird_input in ["", "abc", "1; DROP TABLE accounts", None, 3.14]:
        assert get_account(db, weird_input) is None


def test_lookup_does_not_mutate_data(db: sqlite3.Connection) -> None:
    # A read should never change the number of stored accounts.
    get_account(db, 1)
    count = db.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
    assert count == 3
