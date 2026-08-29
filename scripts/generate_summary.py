"""Agent 4 — AppSec Summary Agent (communication only).

Gathers the results of every prior stage and asks Claude to write one clear,
developer-friendly summary of the whole security lifecycle. This agent does NOT
perform another review — it explains what happened.

Saves:
    artifacts/appsec-summary.md   (the final PR comment)
"""

from __future__ import annotations

import json

from common import (
    call_claude,
    log,
    read_artifact,
    read_json_artifact,
    read_prompt,
    write_artifact,
)


def _fmt(data: object) -> str:
    return json.dumps(data, indent=2) if data else "(not available / stage skipped)"


def build_context() -> str:
    pr_context = read_json_artifact("pr-context.json", {}) or {}
    review = read_json_artifact("security-review.json", {})
    fix = read_json_artifact("security-fix.json", {})
    verification = read_json_artifact("security-verification.json", {})
    # Prefer the verifier's fresh post-fix run; fall back to the baseline run
    # (e.g. when no finding was made and the later stages were skipped).
    pytest_results = (
        read_artifact("pytest-results-postfix.txt")
        or read_artifact("pytest-results.txt", "(unavailable)")
    )
    bandit_results = (
        read_artifact("bandit-results-postfix.json")
        or read_artifact("bandit-results.json", "(unavailable)")
    )

    return (
        "Summarize the complete AppSec lifecycle for this pull request for the "
        "developer. Some stages may be absent (e.g. no finding was made).\n\n"
        f"## PR metadata (JSON)\n```json\n{_fmt(pr_context)}\n```\n\n"
        f"## Reviewer result (JSON)\n```json\n{_fmt(review)}\n```\n\n"
        f"## Fixer result (JSON)\n```json\n{_fmt(fix)}\n```\n\n"
        f"## Verifier result (JSON)\n```json\n{_fmt(verification)}\n```\n\n"
        f"## pytest results\n```\n{pytest_results}\n```\n\n"
        f"## Bandit (SAST) results (JSON)\n```json\n{bandit_results}\n```\n\n"
        "Respond with the Markdown summary described in your instructions."
    )


def main() -> None:
    system_prompt = read_prompt("security-summary.md")
    summary = call_claude(system_prompt, build_context())
    # This agent returns Markdown directly (not JSON).
    write_artifact("appsec-summary.md", summary.strip() + "\n")
    log("AppSec summary generated.")


if __name__ == "__main__":
    main()
