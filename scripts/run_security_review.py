"""Agent 1 — AI Security Reviewer (read-only).

Assembles the PR context gathered by collect_pr_diff.py plus the deterministic
tool output (pytest + Bandit), asks Claude for a structured security review, and
saves:

    artifacts/security-review.json          (structured result)
    artifacts/security-review-comment.md    (human-readable PR comment)

Job outputs: finding (true/false), title, severity.

This agent NEVER modifies source files.
"""

from __future__ import annotations

from common import (
    call_claude,
    extract_json,
    read_artifact,
    read_prompt,
    set_output,
    write_artifact,
    write_json_artifact,
    log,
)


def build_context() -> str:
    """Assemble everything the reviewer is allowed to see."""
    pr_context = read_artifact("pr-context.json", "{}")
    diff = read_artifact("pr-diff.txt", "(no diff)")
    changed_content = read_artifact("changed-files-content.txt", "(none)")
    pytest_results = read_artifact("pytest-results.txt", "(pytest output unavailable)")
    bandit_results = read_artifact("bandit-results.json", "(bandit output unavailable)")

    return (
        "You are reviewing a pull request. Here is all available context.\n\n"
        f"## PR metadata (JSON)\n{pr_context}\n\n"
        f"## PR diff (base...head)\n```diff\n{diff}\n```\n\n"
        f"## Current content of changed files\n{changed_content}\n\n"
        f"## Deterministic tooling — pytest results\n```\n{pytest_results}\n```\n\n"
        f"## Deterministic tooling — Bandit (SAST) results (JSON)\n"
        f"```json\n{bandit_results}\n```\n\n"
        "Review the change and respond with the JSON object described in your "
        "instructions."
    )


def build_comment(finding: dict) -> str:
    """Render the reviewer's finding as a Markdown PR comment (deterministic)."""
    if not finding.get("finding"):
        return (
            "## AI Security Review\n\n"
            "No significant, evidence-backed security issue was identified in "
            "the changes introduced by this pull request.\n\n"
            "### Status\nNO FINDING\n\n"
            "_Deterministic checks (pytest, Bandit) still apply — this only "
            "reflects the AI reviewer's read-only assessment._"
        )
    return (
        "## AI Security Review\n\n"
        "### Finding\n"
        f"**{finding.get('severity', 'UNKNOWN')} — {finding.get('title', 'Security issue')}**\n\n"
        f"**File:** `{finding.get('file', 'unknown')}`"
        + (f" (`{finding['function']}`)" if finding.get("function") else "")
        + "\n\n"
        f"**CWE:** {finding.get('cwe', 'N/A')}\n\n"
        "### Why this matters\n"
        f"{finding.get('risk', 'Not provided.')}\n\n"
        "### Evidence\n"
        f"{finding.get('evidence', 'Not provided.')}\n\n"
        "### Recommendation\n"
        f"{finding.get('recommendation', 'Not provided.')}\n\n"
        "### Confidence\n"
        f"{finding.get('confidence', 'UNKNOWN')}\n\n"
        "### Status\n"
        f"{finding.get('status', 'FIX_REQUIRED').replace('_', ' ')}"
    )


def main() -> None:
    system_prompt = read_prompt("security-reviewer.md")
    result = extract_json(call_claude(system_prompt, build_context()))

    write_json_artifact("security-review.json", result)
    write_artifact("security-review-comment.md", build_comment(result) + "\n")

    has_finding = bool(result.get("finding"))
    set_output("finding", "true" if has_finding else "false")
    set_output("title", result.get("title", ""))
    set_output("severity", result.get("severity", ""))
    log(f"Review complete. finding={has_finding}")


if __name__ == "__main__":
    main()
