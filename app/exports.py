"""Account note read helper (demo)."""
from __future__ import annotations

from pathlib import Path

EXPORT_DIR = Path("exports")


def read_account_note(filename: str) -> str:
    # VULNERABLE (demo only): filename is joined without validation, so an
    # input like "../../etc/passwd" escapes EXPORT_DIR (path traversal).
    return (EXPORT_DIR / filename).read_text(encoding="utf-8")
tests/test_exports.py:
import pytest

from app import exports
from app.exports import read_account_note


def test_read_account_note_blocks_path_traversal(tmp_path, monkeypatch):
    export_dir = tmp_path / "exports"
    export_dir.mkdir()
    (export_dir / "note.txt").write_text("account note", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("TOP SECRET", encoding="utf-8")
    monkeypatch.setattr(exports, "EXPORT_DIR", export_dir)

    assert read_account_note("note.txt") == "account note"   # legit read works
    with pytest.raises(ValueError):                           # traversal refused
        read_account_note("../secret.txt")
