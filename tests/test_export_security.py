"""Security regression tests for the account note export helper.

These tests assert that :func:`app.export.read_account_note` refuses to read
files outside of ``EXPORT_DIR``. They are safe and local: no file outside the
export directory is ever read, because the traversal inputs must be rejected
before any I/O happens.
"""

from __future__ import annotations

import pytest

from app.export import read_account_note


@pytest.mark.parametrize(
    "payload",
    [
        "../../etc/passwd",
        "../secrets.txt",
        "/etc/shadow",
        "subdir/../../note.txt",
        "note.txt/../../../etc/passwd",
    ],
)
def test_read_account_note_rejects_path_traversal(payload: str) -> None:
    """Traversal or absolute paths must be rejected, not read."""
    with pytest.raises(ValueError):
        read_account_note(payload)


def test_read_account_note_reads_file_inside_export_dir(tmp_path, monkeypatch) -> None:
    """A well-formed filename inside the export directory still works."""
    import app.export as export

    monkeypatch.setattr(export, "EXPORT_DIR", tmp_path)
    (tmp_path / "note-1.txt").write_text("hello", encoding="utf-8")

    assert export.read_account_note("note-1.txt") == "hello"
