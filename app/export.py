"""Account note read helper (demo)."""
from __future__ import annotations

import re
from pathlib import Path

EXPORT_DIR = Path("exports")

# Exported notes are plain text files with simple, generated names.
_SAFE_FILENAME = re.compile(r"[A-Za-z0-9_-]+\.txt")


def read_account_note(filename: str) -> str:
    # The filename is checked against an allow-list and the resolved path is
    # constrained to EXPORT_DIR, so inputs like "../../etc/passwd" or an
    # absolute path are rejected instead of escaping the export directory.
    if not _SAFE_FILENAME.fullmatch(filename):
        raise ValueError("invalid filename")

    base = EXPORT_DIR.resolve()
    target = (base / filename).resolve()
    if base not in target.parents:
        raise ValueError("invalid filename")

    return target.read_text(encoding="utf-8")
