"""Account lookup for the GlobalTech Customer Account Service.

This is the *secure baseline* that lives on ``main``. The lookup uses a
parameterized SQL query so that user-controlled input can never change the
structure of the statement that runs.

The instructor deliberately breaks this function on a demo branch (see the
README) by swapping the parameterized query for unsafe string interpolation.
The AI AppSec workflow is then expected to find, fix and verify that change.
"""

from __future__ import annotations

import sqlite3
from typing import Optional, Tuple

# A row is (id, name, email); ``None`` means "no such account".
Account = Optional[Tuple[int, str, str]]


def get_account(db: sqlite3.Connection, account_id: object) -> Account:
    """Look up a single account by its identifier.

    The ``account_id`` is passed to SQLite as a *bound parameter* (the ``?``
    placeholder), never concatenated into the SQL text. SQLite therefore treats
    it purely as a value: it can never alter the query structure, so classic
    SQL-injection payloads simply fail to match any row.

    Args:
        db: An open, seeded SQLite connection (see :mod:`app.database`).
        account_id: The identifier to look up. Accepts any value the caller
            supplies; untrusted input is safe because it is bound, not
            interpolated.

    Returns:
        The matching ``(id, name, email)`` tuple, or ``None`` if no account
        matches (including when the input is malformed).
    """
    return db.execute(
        "SELECT id, name, email FROM accounts WHERE id = ?", (account_id,)
    ).fetchone()
