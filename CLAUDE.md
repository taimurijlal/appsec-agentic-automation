# CLAUDE.md — Guardrails for AI Assistants Working in This Repository

This file tells any AI coding assistant (including Claude Code) how to behave
when editing this repository. **Read it before making changes.**

## What this repository is

This is a **defensive cybersecurity training lab**. It demonstrates an
AI-augmented Application Security (AppSec) workflow on a pull request:
deterministic tooling runs first, then AI agents review, fix, independently
verify, and summarize a security issue — while a human keeps final control.

It is used for teaching CISOs, security leaders, and AppSec professionals.
Clarity and safety matter more than cleverness.

## Hard rules (do not violate)

1. **Defensive only.** Never expand this into offensive tooling. Do not create
   real-world exploit automation, payload generators, scanners aimed at real
   systems, or anything designed to attack infrastructure.
2. **No real targets or secrets.** All data is fictional and uses `.test`
   domains. Never add real credentials, real hostnames, or production access.
   Everything runs against a local, in-memory SQLite database.
3. **Preserve the four-agent separation.** The Reviewer, Fixer, Verifier, and
   Summary agents have distinct, single responsibilities. The agent that writes
   a fix must **never** be the one that certifies it. Keep the Verifier
   independent (fresh checkout, separate job).
4. **Maintain least privilege.** Each GitHub Actions job requests only the
   permissions it needs (see the table in `README.md`). Do not broaden a job's
   permissions. The Fixer must never get merge, deployment, or cloud access.
5. **The AI never merges or deploys.** No job may auto-merge the PR or deploy
   anything. A human developer owns the final merge.
6. **Do not remove the deterministic security checks.** pytest and Bandit run
   before the AI stages. AI *complements* deterministic tooling; it does not
   replace it. Keep them.
7. **Do not weaken loop prevention.** The Fixer commits with the built-in
   `GITHUB_TOKEN` specifically because pushes made with it do not re-trigger the
   workflow. Do not switch to a personal access token or add a trigger that
   would create a workflow loop.
8. **Keep it small and readable.** This is a teaching demo. Favor transparent,
   well-commented scripts and clear YAML over frameworks or hidden logic. Do not
   bury important behavior inside third-party actions.

## Practical notes for edits

- Application code lives in `app/`; tests in `tests/`; agent prompts in
  `prompts/`; orchestration scripts in `scripts/`; the pipeline in
  `.github/workflows/ai-appsec.yml`.
- The secure baseline on `main` uses a **parameterized SQL query**. The demo
  vulnerability is introduced on a branch by the instructor (see README).
- The security regression tests in `tests/test_security.py` must keep the
  property: they **fail** on the vulnerable code and **pass** once a
  parameterized query is restored.
- If you change an agent's contract, update its prompt in `prompts/` and the
  script that consumes its output together, and keep the structured-artifact
  JSON shapes stable.
- Before opening a change, run `pytest` and `bandit -r app`.
