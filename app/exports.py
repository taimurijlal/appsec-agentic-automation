from __future__ import annotations

from pathlib import Path

EXPORT_DIR = Path("exports")


def read_account_note(filename: str) -> str:
    # The filename is confined to EXPORT_DIR: the candidate path is resolved and
    # rejected unless it stays inside the export directory. This blocks both
    # traversal ("../../etc/passwd") and absolute-path inputs.
    base = EXPORT_DIR.resolve()
    target = (base / filename).resolve()
    if target != base and base not in target.parents:
        raise ValueError("invalid filename")
    return target.read_text(encoding="utf-8")
