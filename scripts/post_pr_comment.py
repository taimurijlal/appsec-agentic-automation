"""Post a Markdown file as a pull-request comment via the GitHub REST API.

Kept dependency-free (standard-library ``urllib``) and explicit so students can
see exactly how a comment reaches GitHub — nothing is hidden inside a
third-party action.

Usage:
    python scripts/post_pr_comment.py --file artifacts/security-review-comment.md
    python scripts/post_pr_comment.py --file artifacts/appsec-summary.md --pr 42

Environment (provided by GitHub Actions):
    GITHUB_TOKEN / GH_TOKEN   - token with `pull-requests: write`.
    GITHUB_REPOSITORY         - "owner/repo".
    GITHUB_EVENT_PATH         - event payload (used to infer the PR number).

A PR comment is created through the *issues* comments endpoint, because pull
requests are issues in the GitHub data model.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def infer_pr_number() -> str | None:
    """Read the PR number from the event payload or PR_NUMBER env var."""
    if os.environ.get("PR_NUMBER"):
        return os.environ["PR_NUMBER"]
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if event_path and Path(event_path).exists():
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
        number = event.get("pull_request", {}).get("number") or event.get("number")
        if number is not None:
            return str(number)
    return None


def post_comment(repo: str, pr_number: str, token: str, body: str) -> None:
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    payload = json.dumps({"body": body}).encode("utf-8")
    request = urllib.request.Request(url, data=payload, method="POST")
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    request.add_header("Content-Type", "application/json")
    request.add_header("User-Agent", "ai-appsec-demo")

    # The URL is a fixed https://api.github.com endpoint, not user input.
    with urllib.request.urlopen(request) as response:  # nosec B310
        if response.status not in (200, 201):
            raise SystemExit(f"Unexpected status posting comment: {response.status}")
    print(f"Posted PR comment to {repo}#{pr_number}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Post a Markdown file as a PR comment.")
    parser.add_argument("--file", required=True, help="Path to the Markdown comment body.")
    parser.add_argument("--pr", default=None, help="PR number (else inferred from event).")
    args = parser.parse_args()

    body_path = Path(args.file)
    if not body_path.exists():
        raise SystemExit(f"Comment file not found: {body_path}")
    body = body_path.read_text(encoding="utf-8").strip()
    if not body:
        print("Comment body is empty; nothing to post.", file=sys.stderr)
        return

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    pr_number = args.pr or infer_pr_number()

    if not token or not repo or not pr_number:
        raise SystemExit(
            "Missing GITHUB_TOKEN, GITHUB_REPOSITORY, or PR number — cannot post."
        )

    try:
        post_comment(repo, pr_number, token, body)
    except urllib.error.HTTPError as exc:  # pragma: no cover - network dependent
        detail = exc.read().decode("utf-8", "replace")
        raise SystemExit(f"GitHub API error ({exc.code}): {detail}") from exc


if __name__ == "__main__":
    main()
