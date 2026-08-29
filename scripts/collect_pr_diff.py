"""Collect pull-request context for the AI Security Reviewer.

This is the transparent "what gets passed to the AI" step. It gathers, from the
checked-out repository and the GitHub event payload:

* the PR diff (base...head);
* the list of changed files;
* the current content of changed text files (for surrounding context);
* PR metadata (title, body, number, base/head refs).

Outputs (written to artifacts/):
    pr-diff.txt
    changed-files.txt
    changed-files-content.txt
    pr-context.json

Environment:
    BASE_SHA / HEAD_SHA  - commit range to diff (provided by the workflow).
    GITHUB_EVENT_PATH    - path to the PR event payload (provided by Actions).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from common import REPO_ROOT, log, run, write_artifact

# Only inline the content of reasonably small text files, and skip binaries and
# noise. This keeps the AI context focused and bounded.
MAX_FILE_BYTES = 60_000
SKIP_PREFIXES = ("artifacts/", ".git/")
TEXT_SUFFIXES = (".py", ".txt", ".md", ".toml", ".cfg", ".ini", ".yml", ".yaml", ".json")


def load_pr_context() -> dict:
    """Read PR metadata from the GitHub event payload, if present."""
    context = {"title": "", "body": "", "number": None, "base_ref": "", "head_ref": ""}
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if event_path and Path(event_path).exists():
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
        pr = event.get("pull_request", {})
        context.update(
            title=pr.get("title", ""),
            body=pr.get("body", "") or "",
            number=pr.get("number"),
            base_ref=pr.get("base", {}).get("ref", ""),
            head_ref=pr.get("head", {}).get("ref", ""),
        )
    # Allow explicit overrides / local runs via env vars.
    context["number"] = context["number"] or os.environ.get("PR_NUMBER")
    return context


def diff_range() -> tuple[str, str]:
    """Determine the base and head commits to diff."""
    base = os.environ.get("BASE_SHA", "").strip()
    head = os.environ.get("HEAD_SHA", "").strip() or "HEAD"
    if not base:
        # Local fallback: diff against the merge-base with origin/main.
        base = run(["git", "merge-base", "origin/main", "HEAD"], check=False).strip()
    return base or "HEAD~1", head


def main() -> None:
    context = load_pr_context()
    base, head = diff_range()
    log(f"Diffing {base}..{head}")

    diff = run(["git", "diff", f"{base}", f"{head}"], check=False)
    write_artifact("pr-diff.txt", diff or "(no diff)\n")

    changed = run(["git", "diff", "--name-only", base, head], check=False)
    changed_files = [line.strip() for line in changed.splitlines() if line.strip()]
    write_artifact("changed-files.txt", "\n".join(changed_files) + "\n")

    # Inline the current content of changed text files for context.
    sections: list[str] = []
    for rel_path in changed_files:
        if rel_path.startswith(SKIP_PREFIXES) or not rel_path.endswith(TEXT_SUFFIXES):
            continue
        file_path = REPO_ROOT / rel_path
        if not file_path.exists():
            continue  # deleted in this PR
        data = file_path.read_bytes()
        if len(data) > MAX_FILE_BYTES:
            sections.append(f"### {rel_path}\n(omitted: file larger than "
                            f"{MAX_FILE_BYTES} bytes)\n")
            continue
        sections.append(f"### {rel_path}\n```\n{data.decode('utf-8', 'replace')}\n```\n")

    write_artifact(
        "changed-files-content.txt",
        "\n".join(sections) if sections else "(no changed text files)\n",
    )

    write_artifact(
        "pr-context.json",
        json.dumps(context, indent=2, sort_keys=True) + "\n",
    )
    log(f"Collected {len(changed_files)} changed file(s).")


if __name__ == "__main__":
    main()
