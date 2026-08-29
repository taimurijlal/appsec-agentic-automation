"""Agent 2 — AI Security Fixer (narrowly scoped write access).

Runs only when the reviewer returned a finding. Given the confirmed finding and
the current source, it asks Claude for the smallest correct fix, then writes the
proposed file contents to disk on the PR branch.

Saves:
    artifacts/security-fix.json   (structured result)

Job output: fix_status (proposed / failed / skipped).

Safety guards enforced in code (defense in depth, not just prompt text):
* file paths must resolve inside the repository;
* the fixer may never write to .github/ (workflow / CI security controls);
* if the model declines to fix, we record that honestly.
"""

from __future__ import annotations

import json
from pathlib import Path

from common import (
    REPO_ROOT,
    call_claude,
    die,
    extract_json,
    log,
    read_artifact,
    read_json_artifact,
    read_prompt,
    set_output,
    write_json_artifact,
)

# The fixer is never allowed to touch these paths.
FORBIDDEN_PREFIXES = (".github/", ".git/")


def read_source(rel_path: str) -> str:
    """Read a source file from disk for context, if it exists."""
    path = REPO_ROOT / rel_path
    if not path.exists():
        return f"(not present: {rel_path})"
    return f"### {rel_path}\n```python\n{path.read_text(encoding='utf-8')}\n```"


def build_context(finding: dict) -> str:
    """Assemble the fixer's inputs: the finding, current source, tests, SAST."""
    changed_content = read_artifact("changed-files-content.txt", "(none)")
    # Show the existing security regression test so the fixer knows it already
    # exists and does not duplicate it.
    security_test = read_source("tests/test_security.py")
    bandit_results = read_artifact("bandit-results.json", "(bandit unavailable)")

    return (
        "A security finding has been confirmed. Propose the smallest correct "
        "fix.\n\n"
        f"## Confirmed finding (JSON)\n```json\n{json.dumps(finding, indent=2)}\n```\n\n"
        f"## Current content of changed files\n{changed_content}\n\n"
        f"## Existing security regression test\n{security_test}\n\n"
        f"## Bandit (SAST) results (JSON)\n```json\n{bandit_results}\n```\n\n"
        "Respond with the JSON object described in your instructions, including "
        "the FULL new content of every file you change."
    )


def safe_target(rel_path: str) -> Path:
    """Validate a model-proposed path and return its absolute location.

    A fix should only ever touch relative paths inside the repository. We reject
    absolute paths, parent-directory traversal, and any write under .github/ or
    .git/ — a good habit whenever an AI agent proposes file paths.
    """
    normalized = rel_path.replace("\\", "/")
    if normalized.startswith("/") or (len(normalized) > 1 and normalized[1] == ":"):
        die(f"Fixer proposed an absolute path (rejected): {rel_path!r}")
    if normalized.startswith(FORBIDDEN_PREFIXES) or ".." in Path(normalized).parts:
        die(f"Fixer attempted to write a forbidden path: {rel_path!r}")
    target = (REPO_ROOT / normalized).resolve()
    if REPO_ROOT not in target.parents and target != REPO_ROOT:
        die(f"Fixer attempted to write outside the repository: {rel_path!r}")
    return target


def apply_fix(result: dict) -> list[str]:
    """Write the proposed file contents to disk. Returns the paths changed."""
    written: list[str] = []
    for entry in result.get("files", []):
        rel_path = entry.get("path", "")
        content = entry.get("content")
        if not rel_path or content is None:
            die(f"Malformed file entry in fixer output: {entry!r}")
        target = safe_target(rel_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        written.append(rel_path)
        log(f"Applied fix to: {rel_path}")
    return written


def main() -> None:
    review = read_json_artifact("security-review.json", {}) or {}
    if not review.get("finding"):
        # Defensive: the workflow already gates this job on finding == true.
        set_output("fix_status", "skipped")
        write_json_artifact("security-fix.json", {
            "fix_applied": False, "files": [],
            "summary": "No finding to fix.", "status": "SKIPPED",
        })
        log("No finding present; fixer skipped.")
        return

    system_prompt = read_prompt("security-fixer.md")
    result = extract_json(call_claude(system_prompt, build_context(review)))

    if not result.get("fix_applied"):
        set_output("fix_status", "failed")
        write_json_artifact("security-fix.json", result)
        log("Fixer reported it could not apply a safe fix.")
        return

    written = apply_fix(result)
    # Record what we actually wrote (authoritative over the model's own list).
    result["files_changed"] = written
    write_json_artifact("security-fix.json", result)
    set_output("fix_status", "proposed" if written else "failed")
    log(f"Fix proposed. Files changed: {written}")


if __name__ == "__main__":
    main()
