"""Account note read helper (demo)."""
from __future__ import annotations

from pathlib import Path

EXPORT_DIR = Path("exports")


def read_account_note(filename: str) -> str:
    # The caller-supplied filename is resolved and confined to EXPORT_DIR, so
    # inputs like "../../etc/passwd" or absolute paths cannot escape it.
    base = EXPORT_DIR.resolve()
    target = (base / filename).resolve()
    if not target.is_relative_to(base):
        raise ValueError("Invalid note filename: path escapes the export directory.")
    if not target.is_file():
        raise FileNotFoundError(f"No such account note: {filename}")
    return target.read_text(encoding="utf-8")
