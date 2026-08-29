"""Account note read helper (demo)."""
from __future__ import annotations

from pathlib import Path

EXPORT_DIR = Path("exports")


def read_account_note(filename: str) -> str:
    # The filename must stay inside EXPORT_DIR: resolve both sides and verify
    # containment so inputs like "../../etc/passwd" or "/etc/passwd" are
    # rejected instead of escaping the export directory (path traversal).
    base = Path(EXPORT_DIR).resolve()
    target = (base / filename).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        raise ValueError("invalid filename") from None
    return target.read_text(encoding="utf-8")
