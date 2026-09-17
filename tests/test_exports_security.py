"""Security regression tests for the account note reader.

These tests confirm that :func:`app.exports.read_account_note` only reads
files contained within the export directory. They use a throwaway temporary
directory and fictional data; they are not an exploitation tool.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pytest

from app import exports


@pytest.fixture()
def export_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    directory = tmp_path / "exports"
    directory.mkdir()
    (directory / "note.txt").write_text("hello", encoding="utf-8")
    monkeypatch.setattr(exports, "EXPORT_DIR", directory)
    yield directory


def test_reads_note_inside_export_dir(export_dir: Path) -> None:
    """Legitimate reads inside the export directory still work."""
    assert exports.read_account_note("note.txt") == "hello"


def test_rejects_parent_traversal(export_dir: Path, tmp_path: Path) -> None:
    """A ``..`` segment must not escape the export directory."""
    (tmp_path / "secret.txt").write_text("top secret", encoding="utf-8")
    with pytest.raises(ValueError):
        exports.read_account_note("../secret.txt")


def test_rejects_absolute_path(export_dir: Path, tmp_path: Path) -> None:
    """An absolute filename must not replace the export directory."""
    secret = tmp_path / "secret.txt"
    secret.write_text("top secret", encoding="utf-8")
    with pytest.raises(ValueError):
        exports.read_account_note(str(secret))
