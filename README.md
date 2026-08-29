# AI-Augmented AppSec Pull Request Demo

A small, self-contained teaching lab that shows how a modern Application
Security (AppSec) workflow can combine **GitHub Actions**, **deterministic
security tooling**, and **multiple AI agents** to review a pull request, fix a
security issue, independently verify the fix, and explain the whole lifecycle to
the developer — **without ever auto-merging or deploying**.

> **Audience:** CISOs, security leaders, and AppSec professionals.
>
> **The teaching message:** Existing AppSec controls remain important, but
> frontier AI can increase security-review coverage and shift remediation from
> *"the developer investigates and writes the fix from scratch"* to *"AI proposes
> a fix and the developer verifies it."*
>
> **This is a defensive code-review lab.** All data is fictional, everything runs
> against a local SQLite database, and there is no exploitation tooling.

---

## Overview

The demo models the **GlobalTech Customer Account Service** — a tiny Python app
with one function, `get_account()`. The secure baseline on `main` uses a
**parameterized SQL query**. The instructor introduces a deliberate **SQL
injection** on a branch, opens a pull request, and the pipeline does the rest:

1. **Baseline security checks** — pytest + Bandit run first (deterministic).
2. **AI Security Reviewer** — read-only; finds the issue and posts a finding.
3. **AI Security Fixer** — proposes a minimal patch and commits it to the PR.
4. **Independent Verifier** — a *separate* agent re-checks the fix.
5. **AppSec Summary** — explains everything to the developer.

Four ideas run through it: **AI complements (not replaces) deterministic
tooling**, **AI proposes / independent verification confirms**, **least
privilege applies to AI agents**, and **the developer remains accountable for
the merge**.

---

## Architecture

```
Developer
    │
    ▼
Pull Request  (opened / reopened / synchronized)
    │
    ▼
Baseline Security Checks   ── pytest + Bandit (SAST) ──► artifacts
    │
    ▼
AI Security Reviewer  (read-only)  ──► security-review.json  + PR comment
    │
    ▼  finding = true?
    ▼
AI Security Fixer  (narrow write)  ──► minimal patch committed to PR branch
    │                                   security-fix.json + PR comment
    ▼
Tests + SAST run again  (independently, on the patched branch)
    │
    ▼
Independent AI Security Verifier  (read-only, fresh checkout)
    │                                ──► security-verification.json + PR comment
    ▼
AI AppSec Summary Agent  ──► appsec-summary.md  (final PR comment)
    │
    ▼
Human developer reviews and merges   ◄── nothing is auto-merged or deployed
```

Each stage is a distinct **job** in one workflow (`.github/workflows/ai-appsec.yml`),
wired together with `needs:` so the order is explicit and visible in the GitHub
Actions UI:

```
AI AppSec Pipeline
  ✓ Baseline Security Checks
  ✓ AI Security Reviewer
  ✓ AI Security Fixer
  ✓ Independent Security Verifier
  ✓ AppSec Summary
```

---

## Repository structure

```
.
├── README.md                     # this file
├── CLAUDE.md                     # guardrails for AI assistants editing the repo
├── requirements.txt              # runtime deps (Anthropic SDK)
├── requirements-dev.txt          # + pytest, bandit
├── pyproject.toml                # pytest / bandit config
│
├── app/
│   ├── accounts.py               # get_account() — SECURE parameterized query
│   └── database.py               # local SQLite setup + fictional sample data
│
├── tests/
│   ├── test_accounts.py          # functional tests
│   └── test_security.py          # regression tests (fail on the vuln, pass when fixed)
│
├── prompts/                      # one Markdown contract per AI agent
│   ├── security-reviewer.md
│   ├── security-fixer.md
│   ├── security-verifier.md
│   └── security-summary.md
│
├── scripts/                      # transparent orchestration (no hidden logic)
│   ├── common.py                 # shared helpers (Claude call, JSON, artifacts)
│   ├── collect_pr_diff.py        # gathers exactly what the AI sees
│   ├── run_security_review.py    # Agent 1
│   ├── run_security_fixer.py     # Agent 2  (+ path-safety guards)
│   ├── run_security_verifier.py  # Agent 3
│   ├── generate_summary.py       # Agent 4
│   ├── compose_fix_comment.py    # renders the fixer's PR comment
│   └── post_pr_comment.py        # posts a Markdown file via the GitHub REST API
│
├── artifacts/                    # structured results passed between jobs (gitignored)
└── .github/workflows/ai-appsec.yml
```

---

## Setup

### 1. Create the repository and add these files

Create a new GitHub repository (private is fine) and push this project to it.

```bash
git init
git add .
git commit -m "chore: AI AppSec demo baseline (secure)"
git branch -M main
git remote add origin git@github.com:<you>/<repo>.git
git push -u origin main
```

> ⚠️ **Push with git — not the browser "Upload files" button.** The web uploader
> silently skips dot-folders, including `.github/`, which holds the workflow that
> runs the *entire* pipeline (the #1 cause of "I opened a PR but nothing
> happened"). If you must use the browser, create files via **Add file → Create
> new file** and type the full path (e.g. `.github/workflows/ai-appsec.yml`).
> Also note: pushing anything under `.github/workflows/` over HTTPS requires a
> Personal Access Token with the **`workflow`** scope — or use SSH.

`main` now holds the **secure** baseline (parameterized SQL) and all tests pass.

### 2. Run it locally (recommended before the lesson)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

python -m pytest -ra        # all tests pass on the secure baseline
bandit -r app               # no findings on the secure baseline
```

### 3. Configure the AI provider (GitHub → Settings)

The AI stages call the **Anthropic (Claude) API** directly (see
[Why direct API calls](#why-direct-anthropic-api-calls)).

- **Secret** — `ANTHROPIC_API_KEY`
  Repository → **Settings → Secrets and variables → Actions → Secrets → New
  repository secret**. Name it `ANTHROPIC_API_KEY` and paste your key. The key
  is never hard-coded; only the AI jobs receive it.
- **Variable (optional)** — `ANTHROPIC_MODEL`
  Same page → **Variables → New repository variable**. Set it to the model you
  want (e.g. `claude-opus-5`). If unset, the scripts fall back to a sensible
  default, so the demo is never pinned to one version.
- **Variable (only for identity-linked keys)** — `ANTHROPIC_WORKSPACE_ID`
  Most keys need nothing here. But if your key is *identity-linked* (it can act
  across multiple workspaces), the API returns
  `400 … anthropic-workspace-id is required`. Two ways to resolve it:
  **(a)** the simplest — create a **workspace-scoped** API key instead (no
  variable needed); or **(b)** set an `ANTHROPIC_WORKSPACE_ID` repository
  variable to your workspace id (Anthropic Console → **Settings → Workspaces**).
  The scripts send it automatically when present.

> `GITHUB_TOKEN` is provided automatically by GitHub Actions — you do **not**
> create it. Its per-job permissions are set in the workflow.

---

## Create the demo vulnerability (SQL injection)

On the instructor's machine, create a branch and deliberately replace the safe
query with unsafe string interpolation.

```bash
git checkout main
git checkout -b demo/sql-injection
```

In `app/accounts.py`, replace the **secure** body of `get_account()`:

```python
    # SECURE (baseline on main):
    return db.execute(
        "SELECT id, name, email FROM accounts WHERE id = ?",
        (account_id,),
    ).fetchone()
```

with the **vulnerable** version:

```python
    # VULNERABLE (for the demo only):
    query = f"SELECT id, name, email FROM accounts WHERE id = {account_id}"
    return db.execute(query).fetchone()
```

Then commit and push, and open a pull request into `main`:

```bash
git add .
git commit -m "feature: add account lookup"
git push -u origin demo/sql-injection
```

Open the pull request on GitHub (`demo/sql-injection` → `main`). The workflow
starts automatically.

> Locally you can confirm the demo premise first:
> `python -m pytest tests/test_security.py` **fails** on this branch, and
> `bandit -r app` reports a **B608** SQL-injection finding.

---

## More demo scenarios (optional)

Beyond SQL injection, here are two more vulnerabilities you can demo the same
way. Each **adds** a small feature file plus a regression test on a new branch;
you then open a PR and watch the same review → fix → verify → summary flow. Both
are verified to **fail** on the vulnerable code and **pass** once fixed.

Fastest way to add them in the browser: **Add file → Create new file**, type the
path, paste the code, and choose *"Create a new branch and start a pull
request."* Add the test file to the same branch, then open the PR.

### Scenario B — Hardcoded secret (CWE-798)

*Bandit catches this too (**B105**) — reinforcing "deterministic tooling first,
AI adds the explanation and the fix."*

Add **`app/integrations.py`** (the vulnerable feature):

```python
"""Integration helpers for the GlobalTech risk-scoring API (demo)."""
from __future__ import annotations

# VULNERABLE (demo only): secret hardcoded in source.
RISK_API_TOKEN = "glt_live_9f8a7b6c5d4e3f2a1b0c7d8e9f"


def build_risk_api_headers() -> dict:
    return {"Authorization": f"Bearer {RISK_API_TOKEN}"}
```

Add **`tests/test_integrations.py`** (regression test — fails on the vuln):

```python
from app import integrations
from app.integrations import build_risk_api_headers


def test_token_comes_from_environment(monkeypatch):
    monkeypatch.setenv("GLOBALTECH_RISK_API_TOKEN", "test-token-abc")
    headers = build_risk_api_headers()
    assert headers["Authorization"] == "Bearer test-token-abc", (
        "Secret appears to be hardcoded rather than read from the environment."
    )
```

Expected AI fix — read the token from the environment:

```python
import os

def build_risk_api_headers() -> dict:
    token = os.environ["GLOBALTECH_RISK_API_TOKEN"]
    return {"Authorization": f"Bearer {token}"}
```

*(No new GitHub secret needed — the test injects the value via `monkeypatch`.)*

### Scenario C — Path traversal (CWE-22)

*Bandit **misses** this (no taint analysis) — a great demonstration that **AI
increases coverage beyond SAST**. Here only the AI reviewer and the regression
test catch the flaw.*

Add **`app/exports.py`** (the vulnerable feature):

```python
"""Account note read helper (demo)."""
from __future__ import annotations

from pathlib import Path

EXPORT_DIR = Path("exports")


def read_account_note(filename: str) -> str:
    # VULNERABLE (demo only): filename is joined without validation, so an
    # input like "../../etc/passwd" escapes EXPORT_DIR (path traversal).
    return (EXPORT_DIR / filename).read_text(encoding="utf-8")
```

Add **`tests/test_exports.py`** (regression test — fails on the vuln):

```python
import pytest

from app import exports
from app.exports import read_account_note


def test_read_account_note_blocks_path_traversal(tmp_path, monkeypatch):
    export_dir = tmp_path / "exports"
    export_dir.mkdir()
    (export_dir / "note.txt").write_text("account note", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("TOP SECRET", encoding="utf-8")
    monkeypatch.setattr(exports, "EXPORT_DIR", export_dir)

    assert read_account_note("note.txt") == "account note"   # legit read works
    with pytest.raises(ValueError):                           # traversal refused
        read_account_note("../secret.txt")
```

Expected AI fix — confirm the resolved path stays inside `EXPORT_DIR`:

```python
def read_account_note(filename: str) -> str:
    base = EXPORT_DIR.resolve()
    target = (base / filename).resolve()
    if target != base and base not in target.parents:
        raise ValueError(f"Refusing to read outside the export directory: {filename!r}")
    return target.read_text(encoding="utf-8")
```

### What each scenario shows at the baseline stage

| Scenario | Baseline pytest | Baseline Bandit | AI Reviewer finds it? |
|----------|:---------------:|:---------------:|:---------------------:|
| A — SQL injection (CWE-89) | ❌ fails | ❌ B608 | ✅ |
| B — Hardcoded secret (CWE-798) | ❌ fails | ❌ B105 | ✅ |
| C — Path traversal (CWE-22) | ❌ fails | ✅ **clean (misses it)** | ✅ |

Scenario C is the one to highlight for a security-leadership audience: **the SAST
scan stays green, yet the AI reviewer still catches the flaw** — the clearest
illustration of "AI augments existing controls."

---

## What students should observe

In the pull request, comments appear in this sequence:

1. **AI Security Review** — `HIGH — SQL Injection`, `FIX REQUIRED`.
2. **AI Security Fix** — a patch is committed to the PR branch; tests pass;
   *awaiting verification*.
3. **AI Security Re-Review** — an **independent** agent reports `FIXED`,
   confidence `HIGH`.
4. **AppSec Review Complete** — a single, readable summary: what was introduced,
   what was found, how it was fixed, how it was verified, and that a **human
   must still review and merge**.

Alongside the comments, in the **Actions** tab, students see the five jobs run
in order, each with least-privilege permissions, and the AI fixer's commit
appear on the PR branch. The PR stays **open** — nothing is merged or deployed.

---

## Least privilege for AI agents

Permissions are scoped **per job**, not globally. The workflow starts from
`permissions: {}` (nothing) and each job requests only what it needs.

| Agent (job)          | Read code | Modify PR code | Comment | Merge | Production |
|----------------------|:---------:|:--------------:|:-------:|:-----:|:----------:|
| **Reviewer**         | Yes       | No             | Yes     | No    | No         |
| **Fixer**            | Yes       | Yes            | Yes     | No    | No         |
| **Verifier**         | Yes       | No             | Yes     | No    | No         |
| **Summary**          | Yes       | No             | Yes     | No    | No         |

Concretely, in GitHub Actions terms:

| Job                 | `contents` | `pull-requests` | `issues` |
|---------------------|:----------:|:---------------:|:--------:|
| `baseline-security` | read       | —               | —        |
| `security-review`   | read       | write           | write    |
| `security-fix`      | **write**  | write           | —        |
| `security-verify`   | read       | write           | write    |
| `security-summary`  | read       | write           | write    |

The Fixer is the **only** job with `contents: write`, and it still has **no**
deployment permissions, **no** cloud credentials, and **no** ability to merge.

> **Teaching point:** *Least privilege applies to AI agents just as it applies to
> human users and service identities.* An AI agent should hold the smallest set
> of capabilities its single job requires — and no more.

---

## Safety design

- **Trusted, same-repository pull requests only (v1).** This lab assumes PRs
  come from branches inside the same trusted repository. Do **not** expose AI
  secrets or write-capable tokens to untrusted forked pull requests, and do
  **not** adopt dangerous patterns such as checking out untrusted fork code
  under elevated `pull_request_target` permissions.
- **No workflow loops.** The Fixer commits with the built-in `GITHUB_TOKEN`.
  GitHub deliberately does **not** start a new workflow run for pushes made with
  `GITHUB_TOKEN`, so the Fixer's own commit cannot re-trigger this workflow.
  (Using a personal access token would break this — don't.) The current run
  continues straight through to verification and summary. A `concurrency` group
  also cancels superseded runs on the same PR.
- **Structured state, not scraped comments.** Stages pass data as JSON
  artifacts (`security-review.json`, `security-fix.json`,
  `security-verification.json`, …), never by parsing each other's PR comments.
  **PR comments are for humans; artifacts are for the workflow.**
- **Independent verification.** The Verifier runs in a separate job with a fresh
  checkout of the patched branch and re-runs the tests itself. The agent that
  wrote the fix never certifies it.
- **Graceful failure.** If no issue is found, the Fixer and Verifier are
  skipped and the summary says so. If remediation fails, or tests fail after the
  patch, or the Verifier does not return `FIXED`, the pipeline says **human
  review is required** rather than pretending success. It does **not** loop the
  patch back through the Fixer repeatedly.

---

## Making this repository public

Publishing this repo is **safe from a secrets and content standpoint**:

- The Anthropic API key is **never in the code** — it lives in a GitHub Actions
  **secret**, which stays private even on a public repository.
- There are **no real credentials, hosts, or data** (fictional `.test` data,
  local SQLite only) and **no exploitation tooling** — the SQL-injection example
  is a defensive teaching artifact, and `main` is secure.
- The workflow uses the ordinary `pull_request` trigger, **not** the dangerous
  `pull_request_target` pattern.

**Your secret cannot leak to a stranger's pull request.** GitHub withholds
secrets from workflows triggered by *forked* PRs and downgrades `GITHUB_TOKEN`
to **read-only** for them. On a fork PR the AI steps simply fail (no key), the
Fixer cannot push, and no comments are posted — a fail-safe.

**The one caveat — fork PRs run contributor code.** On a public repo, anyone can
fork it and open a PR, which makes the workflow check out and *execute* their
code on a runner (`pip install`, `pytest`, the scripts). Even with no secrets
and a read-only token, that is untrusted code on a runner — a bounded but
non-zero risk (e.g. compute abuse). Mitigate it:

- **Keep GitHub's fork-PR approval gate on** (default): *Settings → Actions →
  General → "Fork pull request workflows from outside collaborators" → Require
  approval for first-time contributors* — or tighten to *all outside
  collaborators*. Runs from strangers then wait for your approval.
- This lab is explicitly designed for **trusted, same-repository PRs**, so this
  matches its intended threat model.

**Recommendation:** share the code publicly if you like (with the approval gate
on), but for **running the live demo**, prefer a **private** repository (or a
private copy) so the untrusted-fork surface is removed entirely and the
"trusted same-repo PR" assumption holds exactly.

> **Teaching point:** the same secret you would apply to a human contributor —
> *don't run untrusted code with privileges* — applies to an AI-driven pipeline.
> Least privilege and a human approval gate are what make automation on a public
> repo safe.

---

## Why direct Anthropic API calls?

The demo calls the Claude **Messages API** directly from small Python scripts
(via the official `anthropic` SDK) rather than wrapping everything in a
prepackaged action. This is deliberate, for teaching:

- **Structured outputs.** Each agent returns a specific JSON shape that later
  jobs consume. Direct calls give precise control over that contract.
- **Transparency.** Students can read exactly *what context is sent to the AI*,
  *what each agent may and may not do*, *how outputs are saved*, and *how
  decisions pass between jobs* — none of it hidden inside a third-party action.

The model is configurable via the `ANTHROPIC_MODEL` repository variable, so the
lab is never locked to a single version.

---

## Teaching points (recap)

- AI does **not** replace SAST — it runs *after* and *uses* deterministic tools.
- The **Reviewer is read-only**; it cannot change code.
- The **Fixer** has **narrowly scoped** write permissions and cannot merge or
  deploy.
- The **Verifier is independent** — no self-certification.
- **AI never merges.** The **developer remains accountable**.
- Evidence is **auditable** (structured artifacts + PR comments).
- **AI proposes; humans verify.** The goal is to shorten the time from
  vulnerability discovery to *verified* remediation — not to remove the human.

---

## Manual configuration checklist

Before the first live run, make sure you have:

- [ ] Pushed the secure baseline to `main`.
- [ ] Added the `ANTHROPIC_API_KEY` repository **secret** (use a
      **workspace-scoped** key, or set `ANTHROPIC_WORKSPACE_ID` if your key is
      identity-linked — see Setup step 3).
- [ ] (Optional) Set the `ANTHROPIC_MODEL` repository **variable**.
- [ ] Pushed with **git** (or created files via the web *editor*), so `.github/`
      actually made it to the repo — the browser upload button skips it.
- [ ] Confirmed Actions are enabled, and that workflows are allowed to write to
      pull requests (**Settings → Actions → General → Workflow permissions**).
      The per-job `permissions:` blocks handle scoping, but the repository must
      permit write-capable workflows for the same-repo PR flow.
- [ ] Created the `demo/sql-injection` branch and opened a PR when you're ready
      to demonstrate.
