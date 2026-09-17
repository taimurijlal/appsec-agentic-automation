"""Account note read helper (demo)."""
from __future__ import annotations

from pathlib import Path

EXPORT_DIR = Path("exports")


def read_account_note(filename: str) -> str:
    # VULNERABLE (demo only): filename is joined without validation, so an
    # input like "../../etc/passwd" escapes EXPORT_DIR (path traversal).
    return (EXPORT_DIR / filename).read_text(encoding="utf-8")
