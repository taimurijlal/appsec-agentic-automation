"""Local SQLite database setup for the GlobalTech Customer Account Service.

Everything here is intentionally small, deterministic and local:

* the database is SQLite (in-memory by default);
* the sample data is entirely fictional and uses ``.test`` email addresses;
* nothing here connects to a real service or uses real credentials.

The functions below give tests and scripts a repeatable way to build a seeded
database without any external dependencies.
"""

from __future__ import annotations

import sqlite3
from typing import Iterable, Tuple

# Fictional sample accounts: (id, name, email).
# `.test` is a reserved TLD (RFC 6761) and can never resolve to a real host.
SAMPLE_ACCOUNTS: Tuple[Tuple[int, str, str], ...] = (
    (1, "Alice Example", "alice@example.test"),
    (2, "Bob Example", "bob@example.test"),
    (3, "Carol Example", "carol@example.test"),
)


def init_db(
    connection: sqlite3.Connection,
    accounts: Iterable[Tuple[int, str, str]] = SAMPLE_ACCOUNTS,
) -> sqlite3.Connection:
    """Create the ``accounts`` table and seed it with fictional data.

    Args:
        connection: An open SQLite connection to initialise.
        accounts: Rows to insert. Defaults to :data:`SAMPLE_ACCOUNTS`.

    Returns:
        The same connection, now containing a seeded ``accounts`` table.
    """
    connection.execute("DROP TABLE IF EXISTS accounts")
    connection.execute(
        """
        CREATE TABLE accounts (
            id    INTEGER PRIMARY KEY,
            name  TEXT NOT NULL,
            email TEXT NOT NULL
        )
        """
    )
    connection.executemany(
        "INSERT INTO accounts (id, name, email) VALUES (?, ?, ?)",
        accounts,
    )
    connection.commit()
    return connection


def get_connection(database_path: str = ":memory:") -> sqlite3.Connection:
    """Open a seeded SQLite connection.

    Args:
        database_path: Path to a SQLite file, or ``":memory:"`` (default) for a
            throwaway in-memory database. Tests use the in-memory form so runs
            stay fast, isolated and deterministic.

    Returns:
        A connection whose ``accounts`` table has already been seeded.
    """
    connection = sqlite3.connect(database_path)
    # Return rows as tuples of (id, name, email); the simple default is fine
    # for this demo and keeps the query results easy to reason about.
    return init_db(connection)
