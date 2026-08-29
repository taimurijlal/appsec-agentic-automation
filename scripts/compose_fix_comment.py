"""Compose the "AI Security Fix" PR comment from the fixer's structured result.

Kept as its own small, readable step (rather than inline shell) so the workflow
YAML stays easy to read on screen. Reads artifacts/security-fix.json and two
environment inputs describing what validation found, then writes
artifacts/security-fix-comment.md.

Environment:
    TESTS_RESULT  - "pass" | "fail" | "" (empty when the fixer produced no patch)
    COMMITTED     - "true" when the patch was committed to the PR branch
"""

from __future__ import annotations

import os

from common import log, read_json_artifact, write_artifact


def sast_status() -> str:
    """Report the post-fix Bandit result as PASS/FAIL based on findings count."""
    bandit = read_json_artifact("bandit-results.json")
    if bandit is None:
        return "not re-run"
    return "PASS" if not bandit.get("results") else "FAIL"


def main() -> None:
    fix = read_json_artifact("security-fix.json", {}) or {}
    tests_result = os.environ.get("TESTS_RESULT", "").strip().lower()
    committed = os.environ.get("COMMITTED", "").strip().lower() == "true"

    if not fix.get("fix_applied"):
        comment = (
            "## AI Security Fix\n\n"
            "Automated remediation failed: the AI fixer could not produce a "
            "safe, minimal patch for the confirmed finding.\n\n"
            f"### Details\n{fix.get('summary', '(no details provided)')}\n\n"
            "### Status\nHUMAN REVIEW REQUIRED"
        )
        write_artifact("security-fix-comment.md", comment + "\n")
        log("Composed fix comment: remediation failed.")
        return

    files_changed = fix.get("files_changed") or [
        f.get("path") for f in fix.get("files", [])
    ]
    changes = "\n".join(f"- `{path}`" for path in files_changed) or "- (none)"

    if tests_result == "pass":
        validation = f"- Unit tests: PASS\n- SAST (Bandit): {sast_status()}"
        status = "AWAITING INDEPENDENT SECURITY VERIFICATION"
    else:
        validation = f"- Unit tests: FAIL\n- SAST (Bandit): {sast_status()}"
        status = "AUTOMATED REMEDIATION FAILED VALIDATION — HUMAN REVIEW REQUIRED"

    commit_note = (
        "The patch was committed to the pull-request branch."
        if committed
        else "The patch was **not** committed (validation did not pass)."
    )

    comment = (
        "## AI Security Fix\n\n"
        f"{commit_note}\n\n"
        "### Changes\n"
        f"{changes}\n\n"
        "### Summary\n"
        f"{fix.get('summary', '(none)')}\n\n"
        "### Validation\n"
        f"{validation}\n\n"
        "### Status\n"
        f"{status}"
    )
    write_artifact("security-fix-comment.md", comment + "\n")
    log(f"Composed fix comment (tests={tests_result}, committed={committed}).")


if __name__ == "__main__":
    main()
