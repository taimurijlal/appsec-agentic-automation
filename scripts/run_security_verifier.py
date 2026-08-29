"""Agent 3 — Independent AI Security Verifier (read-only, fresh checkout).

Runs in a separate job with a fresh checkout of the (now patched) PR branch, so
the agent that wrote the fix does not certify its own work. Given the original
finding, the fixer's diff, the remediated source, and post-fix pytest + Bandit
results, it decides FIXED / NOT_FIXED / NEEDS_HUMAN_REVIEW.

Saves:
    artifacts/security-verification.json
    artifacts/security-verification-comment.md

Job output: verdict.
"""

from __future__ import annotations

import json

from common import (
    REPO_ROOT,
    call_claude,
    extract_json,
    log,
    read_artifact,
    read_json_artifact,
    read_prompt,
    set_output,
    write_artifact,
    write_json_artifact,
)


def build_context() -> str:
    original_finding = read_json_artifact("security-review.json", {}) or {}
    fix_result = read_json_artifact("security-fix.json", {}) or {}
    fix_diff = read_artifact("security-fix.diff", "(diff unavailable)")
    pytest_results = read_artifact("pytest-results.txt", "(pytest output unavailable)")
    bandit_results = read_artifact("bandit-results.json", "(bandit output unavailable)")

    # Read the current (remediated) content of the file named in the finding.
    remediated = "(source unavailable)"
    file_rel = original_finding.get("file")
    if file_rel and (REPO_ROOT / file_rel).exists():
        remediated = (REPO_ROOT / file_rel).read_text(encoding="utf-8")

    return (
        "Independently verify the remediation. Do not assume it is correct.\n\n"
        f"## Original finding (JSON)\n```json\n{json.dumps(original_finding, indent=2)}\n```\n\n"
        f"## Fixer's reported change (JSON)\n```json\n{json.dumps(fix_result, indent=2)}\n```\n\n"
        f"## Diff introduced by the fixer\n```diff\n{fix_diff}\n```\n\n"
        f"## Current (remediated) content of {file_rel or 'the affected file'}\n"
        f"```python\n{remediated}\n```\n\n"
        f"## Post-fix pytest results\n```\n{pytest_results}\n```\n\n"
        f"## Post-fix Bandit (SAST) results (JSON)\n```json\n{bandit_results}\n```\n\n"
        "Respond with the JSON object described in your instructions."
    )


def build_comment(verification: dict, original: dict) -> str:
    status = verification.get("status", "NEEDS_HUMAN_REVIEW")
    status_line = {
        "FIXED": "SECURITY VERIFICATION PASSED",
        "NOT_FIXED": "SECURITY VERIFICATION FAILED — HUMAN REVIEW REQUIRED",
        "NEEDS_HUMAN_REVIEW": "INCONCLUSIVE — HUMAN REVIEW REQUIRED",
    }.get(status, "HUMAN REVIEW REQUIRED")

    evidence = verification.get("evidence", [])
    if isinstance(evidence, str):
        evidence = [evidence]
    evidence_md = "\n".join(f"- {item}" for item in evidence) or "- (none provided)"

    original_label = (
        f"{original.get('title', 'Security issue')} — {original.get('severity', '')}".strip(" —")
    )

    return (
        "## AI Security Re-Review\n\n"
        "### Original Finding\n"
        f"{original_label}\n\n"
        "### Verification Result\n"
        f"**{status}**\n\n"
        "### Evidence\n"
        f"{evidence_md}\n\n"
        "### Confidence\n"
        f"{verification.get('confidence', 'UNKNOWN')}\n\n"
        "### Residual Risk\n"
        f"{verification.get('residual_risk', 'Not provided.')}\n\n"
        "### Status\n"
        f"{status_line}"
    )


def main() -> None:
    original = read_json_artifact("security-review.json", {}) or {}
    system_prompt = read_prompt("security-verifier.md")
    result = extract_json(call_claude(system_prompt, build_context()))

    write_json_artifact("security-verification.json", result)
    write_artifact("security-verification-comment.md",
                   build_comment(result, original) + "\n")
    set_output("verdict", result.get("status", "NEEDS_HUMAN_REVIEW"))
    log(f"Verification complete. verdict={result.get('status')}")


if __name__ == "__main__":
    main()
